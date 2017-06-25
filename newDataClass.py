from decimal import *
from functions import spinMatchFinder
from functions import convertToSec
 
    
class data:##This is the main data class.
    def __init__(self,ENSDF,ISOvar,option = 'EoL',energyLimit = 999999999, maxSpin = 9):
        ###maybe get rid of option, find out how energy limit and max spin are used

        ##Initialize Parameters
        self.data = []
        self.name = ISOvar
        self.op = option


        ## nucID is what is compared to the first 6 characters of the line to find the correct data
        nucID=self.name.upper()+" "
        ## This while loop makes sure that nucID has the correct leading whitespace to match the data file
        charIndex=0
        while(charIndex<3):
            if nucID[charIndex].isalpha():
                nucID=' '+nucID
            charIndex+=1
        ## if the element symbol is one letter, an additional space must be appended so len(nucID)==6
        if(len(nucID)<6):
            nucID=nucID+' '
            

        ##open the appropriate ensdf file
        self.f = open("Data/"+str(ENSDF),'rU')


        linecount = 0 ## printing linecount can help locate problem-causing lines in the ensdf file
        desiredData = False
        for line in self.f:
            linecount+=1
            ## The line parsing algorithm is derived from the labeling system of the ensdf files
            ## See the endsf manual, pg. 22, for more information about how the lines of data are organized

            ## the for loop must exit when the ensdf switches from evaluated data to experimental results
            ## this is indicated by an empty line in the ensdf file, which is detected her
            if (desiredData and line[0:6].strip() == ''):
                break     

             ## Identifies which lines in the data file have relevant data
            if (line[6:8]==' L' and line[0:6]==nucID):
                #print(linecount,line[:-1])

                ## set desiredData bool so the program wil exit after reading adopted data
                desiredData = True

                ## FINDING THE ENERGY
                energy = line[9:19].strip()

                ## check if valid energy data (i.e. no letter at beginning or end)
                if (energy[0].isalpha() or energy[-1].isalpha()):
                    energy = '-1'

                ## This will handle states with deduced energies enclosed in () 
                deducedEnergy = False
                if '(' in energy:
                    deducedEnergy = True
                    energy = energy.replace('(','')
                    energy = energy.replace(')','')
    
                if 'E' in energy: ## This will convert scientific to decimal notation if needed
                    significand = float(energy[:energy.find('E')])
                    power = 10** float(energy[energy.find('E')+1:])
                    energy = str(significand * power)

                
                ## FINDING THE ENERGY UNCERTAINTY
                uncert = line[19:21].strip()
                ## Set unsert to 0 if no uncertainty is given.
                if (uncert == ''):
                    uncert = '0'
                ## Set uncert to 0 if not numeric 
                elif (not uncert.isnumeric()):
                    uncert = '0'
                
                ## gives uncertainty correct magnitude
                elif ('.' in energy):
                    s = energy.find('.')
                    decimals = energy[s+1:]
                    decimals = Decimal(-len(decimals))
                    uncert = str(Decimal(uncert)*10**decimals)


                ## FINDING ALL SPIN AND PARITY STATES (TO BE FILTERED LATER)
                jpi = line[21:39].strip() 
                ## indicating deduced energy
                if deducedEnergy:
                    jpi = jpi + '**'


                ## FINDING HALF LIFE AND HALF LIFE UNCERTAINTY 
                hlife = line[39:49].strip()
                dhlife = line[49:55].strip()
                
                #FIXME if t1/2 is > 10^9 years, set hlife to 'STABLE'. currently the code is backwards
                if hlife == 'STABLE':
                    #hlife = 3.1536e16 ## 10**9 years in seconds
                    dhlife = [0]

                ## If no half life info is given, hlife is set to -1
                elif hlife == '':
                    hlife = -1
                    dhlife = [0]
                ## CHeck for missing uncertainty
                elif dhlife == '':
                    #FIXME do something here, probbbly crash test this case
                ## Check for non numerical uncertainty
                elif any(char.isalpha() for char in dhlife):
                    print('bogus')
                    #pass
                ## Standard uncertainty
                elif dhlife.isnumeric():                 
                    dhlife = [dhlife,dhlife]
                    if '.' in hlife:
                        s = hlife.split(' ')[0].find('.')
                        decimals = hlife.split(' ')[0][s+1:]
                        decimals = Decimal(-len(decimals))
                        dhlife = [str(Decimal(val)*10**decimals) for val in dhlife]
                    
                    [hlife,dhlife] = convertToSec(hlife,dhlife)
                ## If uncertainty is given as +x-y
                elif dhlife[0] == '+':
                    dhlife = dhlife.split('-')
                    dhlife[0] = dhlife[0].replace('+','')
                    if '.' in hlife:
                        s = hlife.split(' ')[0].find('.')
                        decimals = hlife.split(' ')[0][s+1:]
                        decimals = Decimal(-len(decimals))
                        dhlife = [str(Decimal(val)*10**decimals) for val in dhlife]
                    [hlife,dhlife] = convertToSec(hlife,dhlife)
                ## Not sure if the following case ever appears in the data
                elif dhlife[0] == '-':
                    float('Crash dat shit, brah')
                                

                if(float(energy)<=energyLimit):
                    #include the data #FIXME half lives
                    self.data.append([energy,jpi,uncert])
                    #print(str(linecount)+' :'+str(self.data[-1]))
                else:
                    break

    ## extraTitleText would be desired spin states, for example
    def export(self,fExtOption = '.dat',extraTitleText = ''): 
#            if(fExtOption==".dat"or fExtOption=="_Fil.dat"):##To make data files for use in gnuplot and plt file.
            fileName=str(self.name.upper())+extraTitleText+fExtOption##creates filename
            fileName="Output/" + "gnuPlot/"+fileName.replace('/','_')
            datFile = open(fileName,'wb')##Creates a file with a valid file name.
            for i in range(len(self.data)):
                datFile.write(str.encode(str(self.name)+';'+str(self.data[i][0])+';'+str(self.data[i][1])+';'+str(self.data[i][2])+'\n'))


    def filterData(self,userInput,UI=False):
        ## no spin input
        if (userInput == ''):
            #print(self.data)
            if (not self.data):
                if(UI):
                    pass
                    ## Prints a statement telling user than no file was found
                    #print("Warning:No data filtered/selected for "+ self.name +".")
                self.data=[[0.0,"--",0.0]]##Enters a dummy entry to file with something.
                
        #if(self.op == 'EoL'):
        ## Filter by spin states
        else:
            if (self.data): ## If self.data has data in it
                newData = []
                groundSt = self.data[0]
                for wantedString in userInput.split(","):##adds all the strings that are included in the userInput.
                    for i in range(1,len(self.data)): 
                        #print(self.name,self.data[i])
                        ## The spinMatchFinder will identify if the state is the desired spin
                        if(spinMatchFinder(wantedString, self.data[i][1])):
                            newData.append(self.data[i])
                self.data=newData##changes data to the new data.
                if (self.data):
                    self.data.insert(0,groundSt)
                else:
                    self.data = [[0.0,"--",0.0]]##Enters a dummy entry to file with something.

            else: ## If self.data is empty
                if(UI):
                    ## Prints a statement telling user than no file was found
                    pass
                    #print("Warning:No data filtered/selected for "+ self.name +".")#Prints a statement telling user than no file was found
                self.data=[[0.0,"--",0.0]]##Enters a dummy entry to file with something.
