#Python file created to use as a pipeline script for Genome assembly
#Python script is used to write a PBS file that can be submitted to run rCorrector and BBDuk trim jobs
#Erik Barroso 8/8/2017

import csv
import os, sys
import argparse

#TODO 8/10
#---------
#Check if Trimmings directory exists (if statement by mkdir)
#Add FastQC, check if tag is included in args (--fastQC *path 2 fastQC software*)
#^Create new file within Trimmings for FastQC reports
#TRY catch if directories are already created (Trimmings, fastQC)


#Function is passed a .csv file and the name of the folder containing the data files
#returns two comma seperated strings that hold the input file and folder name to be executed for rCorrector
#returns two arrays that hold the file names from the output of rCorrector trimming
#returns two arrays that hold corresponding output file names 
def pairedFileNames(File, data_Folder):
	in1 = []
	in2 = []
	out1 = []
	out2 = []
	temp = []
	i = 1
	with open(File, 'rb') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			line = list(row)
			in1.append(line[0])
			in2.append(line[1])
			
			#create out1 and out2 as list variables that can be passed into .pbs
			#Then be looped through in BBDuk execution loop
			#Might need to add "trimmedSamples/" folder extension
			temp = (line[0]).split(".")
			suffix = temp[-1]
			if(suffix == "fasta"):
				newSuffix = "fa"
			if(suffix == "fastq"):
				newSuffix = "fq"
			
			corSuffix = "cor." + newSuffix
			out1.append(line[0].replace(suffix, corSuffix))
			out2.append(line[1].replace(suffix, corSuffix))            
			i += 1
			
	NumFiles = len(in1)
    #Creates string out of file names because rCorrector takes input as string seperated by ","
	left = ""
	right = ""
	
	for i in range(NumFiles):
		if(i < NumFiles-1):
			left += data_Folder + "/" + in1[i] + ","
			right += data_Folder + "/" + in2[i] + ","
		else:
			left += data_Folder + "/" + in1[i]
			right += data_Folder + "/" + in2[i]
	return left, right, out1, out2



def tempVariables(path):
    #Given a path name this function returns the name of the last folder in the path
    #This is used to navigate within the PBS file between folders copied into the $TMPDIR
    temp = path.split("/")
    return temp[-1]


#function checks if file or folders exist
#returns error message if folder/path can not be located
def checkFiles(cwd, home, directory):
	path = cwd[:(cwd.find(home))] + home + "/" + directory
	if(os.path.exists(path) == False):
		print "\nCould not find %s from home directory, please check that the file is there and the path entered is correct" % directory
		print "searching for %s in %s\n" % (directory, path)
	else:
		return
	return

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='This script will run trimming using rCorrector and BBduk on raw RNA data Author Erik \n Contact barroso.5 AT osu.edu')
	parser.add_argument('-i', '--input', help='name of csv file holding file names of data to trim, should be in same folder as this script, if not include path from this')
	parser.add_argument('-d','--data', help='path from home project space to location of raw data needed to be trimmed. ex: AglycinesData/AshleyRawdataRNA', required=True)
	parser.add_argument('-r','--rCorrector', help='path from home project space to location of rCorrector software folder. ex: software/rCorrector', required=True)
	parser.add_argument('-bb','--bbmap', help='path from home project space to location of bbmap software folder. ex: software/bbmap', required=True)
	parser.add_argument('--home', help='location where all folders are stored (data folder, software folder, script folder). ex: osu8548', required=True)
	parser.add_argument('-qc', '--fastQC', help='path from home project space to location of fastQC software folder', required=False)
	
	args = parser.parse_args()
	
	inFile = args.input
	data_dir = args.data
	rCorrector_path = args.rCorrector
	bbmap_path = args.bbmap
	fastQC_path = args.fastQC
	home = args.home

	print "FastQC empty args>%s<" % fastQC_path
	cwd = os.getcwd()

	print "Working directory is: %s" % cwd

	try:
		open(inFile, 'r')
	except IOError:
		print "Could not find '%s', check if you entered the file name correctly, the path is correct, and the permissions allow readability" % inFile

	
	data_Folder = tempVariables(data_dir)
	bbmap_Folder = tempVariables(bbmap_path)
	rCorrector_Folder = tempVariables(rCorrector_path)
	rCorrector_exe = os.path.join(rCorrector_Folder, "run_rcorrector.pl")
	bbduk_exe = os.path.join(bbmap_Folder, "bbduk.sh")
	resource_path = os.path.join(bbmap_Folder, "resources/nextera.fa.gz")
    
	output_path = os.path.join(data_Folder, "Trimmings")
	
	#checkFiles(cwd, home, inFile)
	#checkFiles(cwd, home, data_dir)
	#checkFiles(cwd, home, rCorrector_path)
	#checkFiles(cwd, home, bbmap_path)	
    
	left = "" #string of files for left end reads (comma seperated string)
	right = "" #string of files for right end reads (comma seperated string)
	out1 = [] #array of files that will be created by running rCorrector (LEFT)
	out2 = [] #array of files that will be created by running rCorrector (right)
	
	left, right, out1, out2 = pairedFileNames(inFile, data_Folder)
    #Need to take file as input? or check that this file exists and is readable
	
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #This part of the script writes Trim.pbs, 


	f = open("Trim.pbs","w+") #Or delete ../ and have it created in the scripts file, then qsub from 1 down
    #(Want the PBS file to be created in home project space [osu8548])
    #change name to Trim.pbs if this script includes run for BBDuk
	f.write("#PBS -N rThenBBDuk\n")
	f.write("#PBS -l walltime=5:00:00\n")
	f.write("#PBS -l nodes=1:ppn=28\n")
	f.write("#PBS -j oe\n")
	f.write("cd $PBS_O_WORKDIR\n\n")
	
	if(fastQC_path !="None"):
		checkFiles(cwd, home, fastQC_path)
		f.write("cp -r %s %s %s %s $TMPDIR\n" % (data_dir, bbmap_path, rCorrector_path, fastQC_path))
	else:
		f.write("cp -r %s %s %s $TMPDIR\n" % (data_dir, bbmap_path, rCorrector_path))
	
	f.write("cd $TMPDIR\n")
	f.write("ls\n")
	#f.write("mkdir %s\n\n" % "Trimmings")#Match with output_path on line+8 (cd $TMPDIR/"___")
	#can change to output_path so its in the same data folder 
	
	rCorrectorCommand = 'perl %s -od %s -t 28 -1 %s -2 %s' % (rCorrector_exe, "$TMPDIR/Trimmings", left, right)
	#f.write(rCorrectorCommand + "\n\n")
	
	f.write("cd $TMPDIR/Trimmings \n\n")
	f.write("ls\n")
	data_dir = output_path #data for BBDuk trimming comes from output of rCorrector Trim

	leftFiles = '" "'.join(out1) #string variable holding file names after run through rCorrector
	rightFiles = '" "'.join(out2)
	f.write("leftFiles=%s\n" % ('("' + leftFiles + '")'))
	f.write("rightFiles=%s\n" % ('("' + rightFiles + '")'))
	
	NumFiles = len(out1)#Number of files are to be trimmed by BBDuk

	f.write("for ((i=0; i<=%i; i+=1));\n" % NumFiles)
	f.write("do\n")
	
	trimDetails = "ktrim=r k=23 mink=11 hdist=1 tpe tbo minlen=35 qtrim=rl maq=15 &>std_out${i}.log;"
	#Alter trimDetails if you would like to change the trimming done by BBDuk
	
	BBDukcommand = "../%s -Xmx20g in1=${leftFiles[i]} in2=${rightFiles[i]} out1=left${i}.fastq out2=right${i}.fastq outs=singlton${i}.fastq ref=../%s %s" % (bbduk_exe, resource_path, trimDetails)
			
	f.write("\t" + BBDukcommand + "\n")
	f.write("done\n\n")
	
	
	if(fastQC_path != "None"):
		checkFiles(cwd,home,fastQC_path)
		qcString = ""
		for i in range(NumFiles):
			qcString += "left%i.fastq right%i.fastq " % (i,i)
		fastQC_command = "../fastQC %s--outdir=fastQCreport" % qcString
		
		f.write("mkdir fastQCreport\n")
		
		f.write(fastQC_command+"\n")
		
	f.write("cp -r %s $PBS_O_WORKDIR \n" % "$TMPDIR/Trimmings")
	f.close()
    
