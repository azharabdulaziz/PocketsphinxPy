#!/usr/bin/python
import sys
import subprocess
import os
import errno
from subprocess import Popen
import Error_calc
import my_Error_calc
import StoreResults as dump
from os import path
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *

# Define parameters
ExpName = "TIMIT"    
#SNR_Level = "White50db"

BaseDir = "/Users/Azhar/Desktop/MDC_Experiments/" + ExpName + "/"
TestFileIds = BaseDir + ExpName+"_test.fileids"
BaseWavPath = "/Users/Azhar/Desktop/Exp1/timit/"
AcModel0 =ExpName+"_Clean.cd_cont_200";
AcModel20 =ExpName+"_20dB.cd_cont_200";
AcModel15 =ExpName+"_15dB.cd_cont_200";
AcModel10 =ExpName+"_10dB.cd_cont_200";
AcModel = [AcModel0, AcModel10, AcModel15, AcModel20]
ModelsDir = BaseDir + ExpName+"_Models/"
LM = ModelsDir + "timit_test.lm"
Dic = ModelsDir + "timit.dic"

# Create a decoder with certain model
for currentModel in AcModel:
    AM = ModelsDir + currentModel
    print "Acoustic Model: " + AM
    print "Language Model: " + LM
    print "Dictionary: " + Dic
    
    config = Decoder.default_config()
    config.set_string('-logfn', '/dev/null')
    config.set_string('-hmm', path.join(AM))
    config.set_string('-lm', path.join(LM))
    config.set_string('-dict', path.join(Dic))
    decoder = Decoder(config)
    
    # Start reading Test list
    # SNR_Level = ["wav", "wavWhite5db",]
    for snr in range(0, 55, 5):
        if snr == 0:
            ExpWavPath = BaseWavPath + "wav/"
            outDir = BaseDir+"Results/Clean/" + currentModel + "/"
            wavext = ".wav"
        else:
            ExpWavPath = BaseWavPath + "wav" + str(snr) + "db/"
            outDir = BaseDir+"Results/Noisy_" + str(snr) + "db/" + currentModel + "/"
            wavext = ".wav"
            
        # Check for exist outdir
        if not os.path.exists(os.path.dirname(outDir)):
            try:
                os.makedirs(os.path.dirname(outDir))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
                
        outLattice = outDir + "Lattice/"
        if not os.path.exists(os.path.dirname(outLattice)):
            try:
                os.makedirs(os.path.dirname(outLattice))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise            
        # Start reading Test list
        print "Decoding Test Audio Files for " + ExpWavPath + " using AM " + currentModel
        with open(TestFileIds) as fp:
            FinalResult = {}
            ListOfFinalResults = []
            HypText = []
            for AudioFile_rp in fp:
                decoder.start_utt()
                xx = AudioFile_rp.strip('\n')
                # Remove last white space
                fNameOnly = xx.strip()
#                 This is only required for an4                
                #fNameOnly = xx[::-1].replace("/", "-", 1)[::-1]
                #fNameOnly = fNameOnly.split('/', 1)[-1]
                AudioFile = ExpWavPath + fNameOnly + wavext

                # print ("Decoding File: " +AudioFile)
                # print "File Name Only: " + fNameOnly
                stream = open(AudioFile, 'rb')
                while True:
                    buf = stream.read(1024)
                    if buf:
                        decoder.process_raw(buf, False, False)
                    else:
                        break
                decoder.end_utt()
                hypothesis = decoder.hyp()
                # Extract UttId from fNameOnly to be written in Hyp file
                UttId = fNameOnly
                UttId = UttId[::-1].replace("/", "-", 1)[::-1]
                UttId = UttId.split('/', 2)[-1]
                
                HypText.append(hypothesis.hypstr + " (" + UttId + ")\n") 
                FinalResult = {"Name":fNameOnly, "Hyp": hypothesis.hypstr, "Score": hypothesis.best_score, "Confidence": hypothesis.prob}
                ListOfFinalResults.append(FinalResult)
                #print 'Best hypothesis: ', hypothesis.hypstr, " model score: ", hypothesis.best_score, " confidence: ", hypothesis.prob
                LatticeFile = outLattice + fNameOnly.replace("/",'-')
                #print 'LatticeFile: ' + LatticeFile
                decoder.get_lattice().write(LatticeFile + '.lat')
                decoder.get_lattice().write_htk(LatticeFile + '.htk')
                sys.stdout.write("*")
        # Running perl WER test
        print "\n"
        
        dump.TextWrite(HypText, outDir+currentModel+".txt")
        dump.CSVDictWrite(ListOfFinalResults, outDir+"/All_"+currentModel+".csv")
        hypFile = outDir+currentModel+".txt" 
        RefFile = BaseDir+"RefClean.txt"
        out_File = outDir+"WERReslts_"+currentModel+".txt"
        perl_script = subprocess.Popen(["perl", "./word_align.pl",hypFile, RefFile, out_File])
        perl_script.wait()
        print '\n'
