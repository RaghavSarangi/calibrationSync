"""This module takes in the raw data from the Continuous Read VI, as well as the folder made by TRA_multiscan VI, and generates
a csv file that has the data synced and ready for plot generation."""

import csv, os
import pandas as pd
import tkinter as tk
from tkinter import filedialog as fd

class TimeStamp:

    def __init__(self, timeString):
        timeBits = timeString.split(":")
        self.hour = timeBits[0]
        self.minute = timeBits[1]
        self.second = timeBits[2]       
    
    def getTime(self):
        return ":".join([self.hour, self.minute, self.second])
    
    def timeDifference(self, otherTime):
        assert isinstance(otherTime, TimeStamp)
        hour_diff = int(self.hour) - int(otherTime.hour)
        minute_diff = int(self.minute) - int(otherTime.minute)
        second_diff = int(self.second) - int(otherTime.second)
        return abs(hour_diff*3600 + minute_diff*60 + second_diff)

class TemperatureTable:

    def __init__(self, filepath):
        self.CameraValues = []
        self.parseStartIndex = 0
        self.file = filepath
        file = open(filepath)
        csvreader = csv.reader(file)
        self.columnNames = next(csvreader)

        print()
        for i in range(len(self.columnNames)):
            print("{} : {}".format(i, self.columnNames[i]))
        print()

        self.referenceInstrument = int(input("Enter the relevant column index for this calibration i.e. the temperature reference instrument: "))
        print()
        self.numRows = 0
        self.Data = []
        for row in csvreader:
            self.numRows+=1
            self.Data.append(self.continousReadInstance(row[0], TimeStamp(":".join(row[1].split("."))), row[self.referenceInstrument]))
        file.close()

    # def printTable(self):
    #     print(self.columnNames)
    #     if len(self.CameraValues)!=0:
    #         for i in range(len(self.Data)):
    #             print(self.getData()[i].showInstance(), self.CameraValues[i])
    #     else:
    #         for i in self.Data:
    #             print(i.showInstance())
    
    def getData(self):
        return self.Data
    
    def getParseStartIndex(self):
        return self.parseStartIndex

    def setParseStartIndex(self, index):
        self.parseStartIndex = index
    
    def addValueToCameraValues(self, value):
        self.CameraValues.append(value)
    
    def generateCSVfile(self, path):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Time", self.columnNames[self.referenceInstrument], "Camera"])
            for i in range(len(self.CameraValues)):
                cameraData = self.CameraValues[i]
                if cameraData is None:
                    row = list(self.getData()[i].showInstance())
                else: 
                    row = list(self.getData()[i].showInstance()) + list((cameraData,))
                writer.writerow(row)
    
    class continousReadInstance:

        def __init__(self, Date, time, refTemp):
            self.dateOfReading = "/".join(Date.split(sep="//"))
            self.timeOfReading = time
            self.refTempOfReading = refTemp
        
        def getDateOfReading(self):
            return self.dateOfReading
        
        def getTimeOfReading(self):
            return self.timeOfReading
        
        def getRefTempOfReading(self):
            return self.refTempOfReading
        
        def showInstance(self):
            return(self.getDateOfReading(), self.getTimeOfReading().getTime(), self.getRefTempOfReading())

class runStage:

    def __init__(self, folderPath):
        self.folderPath = folderPath
        elements = folderPath.split(sep="/")
        dateTime = elements[-1].split(sep="_")
        self.runDate  = "/".join(dateTime[:3])
        self.runTime = TimeStamp(":".join(dateTime[-4:-1]))
        self.runBathTemp = dateTime[-1]

        all_files = os.listdir(folderPath)  
        csv_files = list(filter(lambda f: f.endswith('.csv'), all_files))
        csv_files.remove("dataset.csv")
        csv_files.sort()
        tempFile = folderPath + "/dataset.csv"
        df=pd.read_csv(tempFile, sep=',',header=None)
        list_of_temp_values = df[1].to_list()
        self.recordedValues =[]

        # Sometimes, a particular bath temperature creates less csv files than it is supposed to, probably because LabView
        # did not have enough time to do so.
        if len(csv_files) == NumOfSnapshotsPerBathTemp:
            for i in range(1, len(list_of_temp_values)+1):
                date_constructor = csv_files[i].split("_")
                date_constructor[2] = "20" + date_constructor[2]
                date = "/".join(date_constructor[:3]) 
                time = TimeStamp(":".join(csv_files[i].split("_")[3:6]))
                self.recordedValues.append(self.Datum(list_of_temp_values[i-1], date, time))
        else:
            for i in range(1, len(list_of_temp_values)):
                date_constructor = csv_files[i].split("_")
                date_constructor[2] = "20" + date_constructor[2]
                date = "/".join(date_constructor[:3]) 
                time = TimeStamp(":".join(csv_files[i].split("_")[3:6]))
                self.recordedValues.append(self.Datum(list_of_temp_values[i-1], date, time))
            
    def getDate(self):
        return self.runDate
    
    def getBathTemp(self):
        return self.runBathTemp
    
    def getRecordedValues(self):
        return self.recordedValues

    def showStage(self):
        return self.runDate + " " + str(self.runTime.getTime()) + " " + self.runBathTemp
    
    def showData(self):
        for i in self.recordedValues:
            assert isinstance(i, self.Datum)
            print(i.InfoBundle())


    class Datum:

        def __init__(self, temp, date, time):
            self.IRtemperature = temp
            self.recordingDate = date
            self.recordingTime  = time
        
        def getRecordingDate(self):
            return self.recordingDate

        def getRecordingTime(self):
            return self.recordingTime
        
        def getIRTemperature(self):
            return self.IRtemperature
        
        def InfoBundle(self):
            return(self.IRtemperature, self.recordingDate, self.recordingTime.getTime())


def breakUpRun(dataTable, runFolder, csvfilePath):
    assert isinstance(dataTable, TemperatureTable)
    all_folders = os.listdir(runFolder)
    all_folders.remove(".DS_Store")
    all_folders.sort(key= lambda folder: "/".join(folder.split(sep="_")[:3]) + " :".join(folder.split(sep="_")[-4:-1]))
    for folder in all_folders:
            cycle = runStage(runFolder + "/" + folder)
            # print(cycle.showStage())
            for measurement in cycle.getRecordedValues():
                syncValuesForMeasurement(dataTable, measurement)
            # cycle.showData()
    dataTable.generateCSVfile(csvfilePath)

def syncValuesForMeasurement(dataTable, reading):
    assert isinstance(dataTable, TemperatureTable)
    assert isinstance(reading, runStage.Datum)
    for i in range(dataTable.getParseStartIndex(), len(dataTable.getData())):
        row = dataTable.getData()[i]
        if (row.getDateOfReading() == reading.getRecordingDate()) and (row.getTimeOfReading().timeDifference(reading.getRecordingTime())<=0.5*TimeBetweenContinousReadMeasurements):
            # print(row.getTimeOfReading().getTime(), reading.getRecordingTime().getTime(), row.getTimeOfReading().timeDifference(reading.getRecordingTime()))
            dataTable.addValueToCameraValues(reading.getIRTemperature())
            dataTable.setParseStartIndex(i+1)
            return
        else:
            dataTable.addValueToCameraValues(None)

NumOfSnapshotsPerBathTemp = 0
TimeBetweenContinousReadMeasurements = 0
reference_file = "generic"
ICI_folder = "generic"
outputPath = "generic"

### GUI Operations ###
root = tk.Tk()
root.title("Syncing for Calibration")
root.geometry("900x400")

snapNum = tk.IntVar()
time = tk.IntVar()

def checkCondition():
    if snapNum.get() != 0 and time.get() != 0 and reference_file != "generic" and ICI_folder != "generic" and outputPath != "generic":
        return True
    else:
        return False

  
def browseRawDataFile():
    global reference_file
    reference_file = fd.askopenfilename(title='Open a CSV file', filetypes = (('csv files', '*.csv'),))
    reference_file_label.config(text=reference_file)
    if checkCondition():
        sub_btn["state"] = "normal"

def browseTRAMultiscanFolder():
    global ICI_folder
    ICI_folder = fd.askdirectory(title='Open a folder')
    ICI_folder_label.config(text=ICI_folder)
    if checkCondition():
        sub_btn["state"] = "normal"

def browseOutputFolder():
    global outputPath
    outputPath = fd.askdirectory(title='Open a folder')
    outputPath += '/syncedData.csv'
    output_path_label.config(text=outputPath)
    if checkCondition():
        sub_btn["state"] = "normal"

def submit():
    global NumOfSnapshotsPerBathTemp
    global TimeBetweenContinousReadMeasurements

    NumOfSnapshotsPerBathTemp = snapNum.get()
    TimeBetweenContinousReadMeasurements = time.get()
    
    test_table = TemperatureTable(reference_file)
    breakUpRun(test_table, ICI_folder, outputPath)
    root.quit()
     
snapNum_label = tk.Label(root, text = 'Number of snapshots the camera takes at each Bath Temperature:')
snapNum_label.grid(row=0,column=0, padx=10,  pady=10)
snapNum_entry = tk.Entry(root,textvariable = snapNum)
snapNum_entry.grid(row=0,column=2, padx=5,  pady=10)
  
time_label = tk.Label(root, text = 'Number of seconds between each continous read measurement:')
time_label.grid(row=1,column=0, padx=10,  pady=10)
time_entry=tk.Entry(root, textvariable = time)
time_entry.grid(row=1,column=2, padx=5,  pady=10)


browsebutton1 = tk.Button(root, text="Choose the raw data FILE from Continuous_Read", command=browseRawDataFile)
browsebutton1.grid(row=3,column=0, padx=10,  pady=10)
reference_file_label = tk.Label(root)
reference_file_label.grid(row=3,column=2, padx=5,  pady=10)

browsebutton2 = tk.Button(root, text="Choose the FOLDER generated BY TRA_multiscan", command=browseTRAMultiscanFolder)
browsebutton2.grid(row=4,column=0, padx=10,  pady=10)
ICI_folder_label = tk.Label(root)
ICI_folder_label.grid(row=4, column=2, padx=5,  pady=10)

browsebutton3 = tk.Button(root, text="Choose the FOLDER to place the synced CSV file (OUTPUT)", command=browseOutputFolder)
browsebutton3.grid(row=5,column=0, padx=10,  pady=10)
output_path_label = tk.Label(root)
output_path_label.grid(row=5, column=2, padx=5,  pady=10)


sub_btn=tk.Button(root,text = 'SUBMIT', command = submit, fg = 'light green')
sub_btn.grid(row= 9, column = 1, pady = 30)
sub_btn["state"] = "disabled"
  

root.mainloop()
##################