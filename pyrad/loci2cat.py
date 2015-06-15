#!/usr/bin/env python2
""" make cat file output, with site read depth info 
    for all output in the .loci file """

import numpy as np
import os
import sys
import gzip
import cPickle as pickle
import glob


def datstring(obj):
    """ returns string representatin of obj"""
    dat = zip(obj.Cs, obj.As, obj.Ts, obj.Gs)
    stringdat = []
    for site in dat:
        stringdat.append(
            str(site[0])+","+\
            str(site[1])+","+\
            str(site[2])+","+\
            str(site[3]))
    return stringdat


def insertindels(fulldat, arrayed, names, cut1):
    """ inserts indels from the .loci aligned
    locus into the data obj called on consensus
    seqs before alignment """
    for num, site in enumerate(arrayed.T):
        ## check for indels
        who = [names[i] for i, j in enumerate(site) if j == "-"]
        if who:
            for tax in fulldat:
                if tax in who:
                    fulldat[tax].seq = np.insert(tuple(fulldat[tax].seq), 
                                             num+len(cut1), "-").tostring()
                    fulldat[tax].string = np.insert(fulldat[tax].string, 
                                             num+len(cut1), "0,0,0,0").tolist()
                else:
                    fulldat[tax].seq += "-"
                    fulldat[tax].string = np.append(fulldat[tax].string,
                                                     "0,0,0,0").tolist()
                    #print tax, fulldat[tax].seq
                    #print tax, fulldat[tax].string                    
    return fulldat


def make(params, names, quiet):
    """ main func """

    ## get cutter for length
    if "," in params["cut"]:
        cut1 = params["cut"].split(",")[0]
    else:
        cut1 = params["cut"]

    ## check for new2olddict
    picklehandle = params["work"]+"clust"+params["wclust"]+"/"+\
                   params["outname"]+".new2olddict"
    if os.path.exists(picklehandle):
        pickleloc = gzip.open(params["work"]+"clust"+\
                              params["wclust"]+"/"+
                              params["outname"]+".new2olddict", 'rb')
        new2olddict = pickle.load(pickleloc)
        pickleloc.close()
    else:
        sys.exit("\tno locus translator for "+params["outname"]+" data set")
    #for i in range(10):
    #    print new2olddict.items()[i]

    ## read in the old2ids map
    picklehandle = params["work"]+"clust"+params["wclust"]+"/"+\
                   params["outname"]+".new2olddict"
    if os.path.exists(picklehandle):
        pickleloc = gzip.open(params["work"]+"clust"+\
                              params["wclust"]+"/"+
                              "cat.loc2name.map", 'rb')
        old2ids = pickle.load(pickleloc)
        pickleloc.close()
    else:
        sys.exit("\n\tno locus map for "+params["outname"]+"data set")

    #print old2ids

    ## read in all of the bindata
    bindata = glob.glob(params["work"]+"clust"+params["wclust"]+"/*.bindata")
    if not bindata:
        sys.exit("no bin data for "+params["outname"]+"data set")
    else:
        if not quiet:
            sys.stderr.write("\t... loading full sequence data\n")
        ## dictionary for mapping ids to there data
        bindict = {}
        for bindat in bindata:
            sampname = bindat.split("/")[-1].strip(".bindata")
            #print sampname
            ## load bindict object into dictionary
            pickleloc = gzip.open(bindat, 'rb')
            bindict[sampname] = pickle.load(pickleloc)
            pickleloc.close()
    if not quiet:
        sys.stderr.write("\t... matching sequence data files\n")

    ## open output file
    outfile = open(params["work"]+"outfiles/"+\
                   params["outname"]+".catg", 'w')

    ## read in the .loci file
    finalfile = open(params["work"]+"outfiles/"+\
                     params["outname"]+".loci").read() 

    ## get the total length of seqdata
    seqlen = 0
    for loc in finalfile.split("//")[:-1]:
        line1 = loc.split('\n')[1]
        seqlen += len(line1.strip().split()[1])

    print >>outfile, len(names), seqlen
    names = list(names)
    names.sort()
    print >>outfile, " "*len(names)+"\t"+"\t".join(names)

    for locnumber, loc in enumerate(finalfile.split("|\n")[:-1]):
        ## get old locus number
        oldloc = new2olddict[locnumber+1]

        ## get tax id and seq id
        fullids = old2ids[int(oldloc)]

        ## put data obj in a dict
        fulldat = {}
        for sample in fullids:
            tax, cid, end = sample.rsplit("_", 2)
            obj = bindict[tax][cid+"_"+end]
            obj.string = datstring(obj)
            fulldat[tax] = obj

        ## get indels from .loci file
        arrayed = np.array([tuple(i.split()[-1]) for i in \
                            loc.strip().split("\n") if ">" in i])

        # ## correction for potential indels in cut site region
        # for tax in fulldat:
        #     diff = (len(arrayed.T)+len(cut1))-len(fulldat[tax].seq)
        #     if diff > 0:
        #         print arrayed.T
        #         print fulldat[tax].seq
        #         print len(fulldat[tax].seq)
        #         print diff, 'diff'
        #         for i in range(diff):
        #             print "INDELPOP"
        #             temp = list(fulldat[tax].seq)
        #             temp[i] = "-"
        #             fulldat[tax].seq = "".join(temp)
        #             fulldat[tax].string[i] = "0,0,0,0"
        #             #fulldat[tax].seq = np.insert(tuple(fulldat[tax].seq),
        #             #                                0, "-").tostring()
        #             #fulldat[tax].string = np.insert(fulldat[tax].string,
        #             #                                0, "0,0,0,0").tolist()
        #         print fulldat[tax].seq, 'FIX'

        #print fulldat
        #print arrayed
        ## insert indels into sequence
        tnames = [i for i in names if i in fulldat]
        tnames.sort()
        fulldat = insertindels(fulldat, arrayed, tnames, cut1)
        #print fulldat[tax].seq, 'FIX'

        ## write to file
        for site in range(len(cut1), len(arrayed.T)+len(cut1)):
            xseq = []
            xdat = []
            for tax in names:
                if tax in fulldat:
                    xseq.append(fulldat[tax].seq[site].upper())
                    xdat.append(fulldat[tax].string[site])
                else:
                    xseq.append("N")
                    xdat.append("0,0,0,0")
            # print site, tax, fulldat[tax]
            # print fulldat[tax].seq
            # print fulldat[tax].string
            # xseq = [fulldat[tax].seq[site].upper() if tax in fulldat else "N" \
            #                      for tax in names]
            # xdat = [fulldat[tax].string[site] if tax in fulldat else \
            #                    "0,0,0,0" for tax in names]
            print >>outfile, "".join(xseq)+"\t"+"\t".join(xdat)
        #print " "
        
    outfile.close()

if __name__ == "__main__":
    make(params, names, quiet)

