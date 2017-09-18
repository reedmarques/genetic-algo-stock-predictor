# Get bugs out, put display on canvas, make multiple stocks
from yahoo_finance import *
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.finance import date2num
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange

import numpy as np
from numpy import arange

import sys

from tkinter import *
from PIL import Image, ImageTk

import urllib.request
import datetime as dt
import time
from random import *
#Took animation format from the 15-112 website.
# Everything else is written and inspired by myself.



class PullData(object):
    def __init__(self):
        self.stockName = 'JNUG'
        self.stock = Share(self.stockName)
        self.stocksToShow = ['AAPL', 'GOOG', 'JNUG', 'FB']

        self.price = self.stock.get_price()
        self.prevClose = self.stock.get_prev_close()
        self.change = self.stock.get_change()
        
        self.HistoricalInfo = {}
        self.graphHistoricalInfo = {}
        self.startDate = ""
        self.endDate = ""
        self.guessDate = None
        self.guessPrice = None
        self.checkDate = None
        self.checkPrice = None

        self.position = 0
        self.bandPrediction = []
        self.actualBandEvent = []
        self.bandPredictionResult = ""

        self.momentumPrediction = []
        self.momentumPredictionResult = ""
        self.actualMomentumEvent = []

        self.MVAPrediction = []
        self.MVAPredictionResult = ""
        self.actualMVAEvent = []
        self.scoreList = []
        self.iterations = 0

        self.xData = []
        self.yData = []

        self.indicators = ["Outside 10-Bands", "Upward Momentum", "10MVA"] #Each one needs date as a param
        self.bestIndicators = (0, [])
        self.randDates = []
        self.seenDates = set()

        self.prediction = ""


    def getStock(self):
        return self.stockName

    def getDate(self):
        return self.endDate

    def switchStocks(self):
        return self.stocksToShow

    def setStock(self,newStock):
        self.stockName = newStock.upper()
        PullData.resetInfo(self)
        PullData.updateInfo(self)
        print("new stock", self.stockName)

    def setCurrentDate(self,newDate):
        self.endDate = newDate
        #PullData.updateInfo(self)
        return(self.endDate)

    def setStartDate(self,newDate):
        self.startDate = newDate
        PullData.updateInfo(self)
        return(self.startDate)

    def indicatorsLength(self):
        return len(self.indicators)

    def resetInfo(self):
        self.seenDates = set()
        self.position = 0
        self.bandPrediction = []
        self.actualBandEvent = []
        self.bandPredictionResult = ""
        self.momentumPrediction = []
        self.momentumPredictionResult = ""
        self.actualMomentumEvent = []
        self.HistoricalInfo = {}

    def setIterations(self, iterations):
        self.iterations = int(iterations)
        return self.iterations

    def showGraph(self):
        self.xData = []
        self.yData = []
        PullData.getGraphHistorical(self)
        for date in sorted(self.graphHistoricalInfo):
            self.xData += [dt.datetime.strptime(date, '%Y-%m-%d')]
            self.yData += [self.graphHistoricalInfo[date]['Close']]
        # self.xData = np.array([self.xData])
        # self.yData = np.array([self.yData])



        fig, ax = plt.subplots() #Got help from online about how to put dates on graph
        ax.plot(self.xData, self.yData)
        ax.xaxis.set_major_locator(DayLocator())
        ax.xaxis.set_minor_locator(HourLocator(arange(0, 25, 6)))
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))

        ax.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
        fig.autofmt_xdate()
        plt.title(self.stockName)
        plt.grid(True)
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.show()

    def updateInfo(self):
        self.stock = Share(self.stockName)
        self.price = self.stock.get_price()
        self.prevClose = self.stock.get_prev_close()
        self.change = self.stock.get_change()
        PullData.getHistorical(self, self.startDate, self.endDate)


    def getPrice(self):
        return self.price
        
    def getPrevClose(self):
        return(self.prevClose)

    def getChange(self):
        return self.change

    def getGraphHistorical(self): #2D dict of [date][info]
        data = (self.stock.get_historical(self.startDate,self.endDate))

        
        for dict in data:
            date = dict["Date"]
            self.graphHistoricalInfo[date] = dict
        return self.graphHistoricalInfo

    def getHistorical(self,startDate,endDate): #2D dict of [date][info]
        self.startDate = startDate
        #self.endDate = endDate
        data = (self.stock.get_historical(startDate,endDate))

        
        for dict in data:
            date = dict["Date"]
            self.HistoricalInfo[date] = dict
        return self.HistoricalInfo

    def getMVAHistorical(self,startDate,endDate): #2D dict of [date][info]
        self.startDate = startDate
        newData = {}
        data = (self.stock.get_historical(startDate,endDate))

        
        for dict in data:
            date = dict["Date"]
            newData[date] = dict
        return newData

    def outside10Bands(self): #Return Above, Below, or False
        print("guess Date", self.guessDate)
        if self.guessDate in self.seenDates:
            while self.guessDate in self.seenDates:
                rand = randint(0,len(self.HistoricalInfo))-2
                self.guessDate = self.randDates[rand]
                self.checkDate = self.randDates[rand+1]
        MA10 = PullData.findNthDayMVAFromNDaysAgo(self, 10, self.guessDate)
        self.guessPrice = self.HistoricalInfo[self.guessDate]['Close']
        self.seenDates.add(self.guessDate)
        if (float(self.guessPrice) > 1.05*(MA10) or float(self.guessPrice) < .95*(MA10)):
            if float(self.guessPrice) > 1.05*(MA10):
                self.bandPrediction += [(self.guessDate, "Down")]
                return "Down" #Price is above bound so prediction is down
            self.bandPrediction += [(self.guessDate, "Up")]
            return "Up" #Price is below bound so prediction is up
        self.bandPrediction += [(self.guessDate, "False")]
        return False

    def return10BandsData(self): # Returns what stock is predicted to do
        return self.bandPrediction

    def returnActualBandEvent(self): # Returns what stock actually did
        return self.actualBandEvent

    def return10BandsPredictionResult(self):
        return self.bandPredictionResult


    def upwardMomentum(self):
        if self.guessDate in self.seenDates:
            while self.guessDate in self.seenDates:
                rand = randint(0,len(self.HistoricalInfo))-2                
                self.guessDate = self.randDates[rand]                
                self.checkDate = self.randDates[rand+1]                
        MA20 = PullData.findNthDayMVAFromNDaysAgo(self, 20, self.guessDate)        
        MA40 = PullData.findNthDayMVAFromNDaysAgo(self, 40, self.guessDate)        
        self.seenDates.add(self.guessDate)
        if MA20 > MA40:
            self.momentumPrediction += [(self.guessDate, "Up")]
            return "Up"
        self.momentumPrediction += [(self.guessDate, "Down")]
        return "Down"

    def returnMomentumData(self):
        return self.momentumPrediction


    def returnActualMomentumData(self):
        return self.actualMomentumEvent

    def returnMomentumPredictionResult(self):
        return self.momentumPredictionResult


    def test10MVA(self, guessDate):
        if self.guessDate in self.seenDates:
            while self.guessDate in self.seenDates:
                rand = randint(0,len(self.HistoricalInfo))-2
                self.guessDate = self.randDates[rand]
                self.checkDate = self.randDates[rand+1]
        newEndDate = guessDate
        newStartDate = PullData.convertDate(self, 10, newEndDate)
        self.seenDates.add(self.guessDate)
        newData = PullData.getMVAHistorical(self, newStartDate, newEndDate)
        total = 0
        count = 0
        for date in sorted(newData):
            total += float(newData[date]["Close"])
            count += 1
        MA10 = total/count
        self.guessPrice = float(self.HistoricalInfo[self.guessDate]['Close'])
        if self.guessPrice > MA10:
            self.MVAPrediction += [(self.guessDate, "Up")]
            return "Up"
        self.MVAPrediction += [(self.guessDate, "Down")]
        return "Down"

    def returnMVAData(self):
        return self.MVAPrediction

    def returnActualMVAData(self):
        return self.actualMVAEvent

    def returnMVAPredictionResult(self):
        return self.MVAPredictionResult


    def findNthDayMVAFromNDaysAgo(self,n, guessDate):
        newEndDate = guessDate
        newStartDate = PullData.convertDate(self, n, newEndDate)
        newData = PullData.getMVAHistorical(self, newStartDate, newEndDate)
        total = 0
        count = 0
        for date in sorted(newData):
            total += float(newData[date]["Close"])
            count += 1
        MVA = total/count
        return MVA

    def convertDate(self, daysAway, someDay):
        day = (someDay[-2:]) ####
        month = (someDay[5:7]) ####
        year = someDay[:4]
        day = int(day)
        month = int(month)
        weekLength = 5
        weekends = daysAway//weekLength #Adding weekends because market is closed then.
        monthSub = abs((day-daysAway-weekends)//30)
        day = str((day-daysAway-weekends)%30)
        if len(day)==1: day = "0" + day
        month = str(month-monthSub)
        if len(month)==1: month = "0" + month
        
        if int(day) == 0 and int(month) == 3: #February
            day = "28"
            month = "0" + str(int(month)-1)

        elif str(day) == "00" and int(month)%2 == 1 and int(month) <= 7:
            day = "31"
            month = "0" + str(int(month)-1)

        elif str(day) == "00" and int(month)%2 == 1 and int(month) > 7:
            day = "30"
            month = "0" + str(int(month)-1)
        
        elif str(day) == "00" and int(month)%2 == 0 and int(month) <= 7:
            day = "30"
            month = "0" + str(int(month)-1)

        elif str(day) == "00" and int(month)%2 == 0 and int(month) > 7:
            day = "31"
            month = "0" + str(int(month)-1)
        if month == "00":
            month = "12"
            year = str(int(year)-1)

        if len(month)==1: month = "0" + month
        newStartDate = year+"-"+month+"-"+day ####
        return newStartDate

    def findBestIndicators(self): #Getting list combos, guess and check to make accuracy ratio, return best list
        #currentIndicatorTest = [randint(0,1) for i in range(len(self.indicators))]
        currentIndicatorTest = [1,1,1]
        effectiveness = PullData.guessPrice(self, currentIndicatorTest)
        if effectiveness > self.bestIndicators[0]:
            self.bestIndicators = effectiveness, currentIndicatorTest
        return PullData.predictTomorrow(self, currentIndicatorTest)
        
        

    def guessPrice(self, currentIndicatorTest): #Guesses price at 10 random times in past 30 days
        #According to each indicator, it should return True for up and False for down
        self.scoreList = [None]*len(self.indicators)
        correctCount = 0 #Correctcount not Truecount
        incorrectCount = 0
        position = 0
        startDate = PullData.convertDate(self,30, self.endDate)
        self.HistoricalInfo = PullData.getHistorical(self,startDate,self.endDate)
        self.randDates += (sorted(self.HistoricalInfo.keys()))
        for indicator in currentIndicatorTest:
            correctCount = 0
            incorrectCount = 0
            self.seenDates = set()
            if indicator == 1:
                if self.position == 0:
                    for check in range(10): #If more trues than falses, then this indicator succeeded.
                        rand = randint(0,len(self.HistoricalInfo))-2
                        self.guessDate = self.randDates[rand]
                        self.checkDate = self.randDates[rand+1]
                        test = PullData.outside10Bands(self) == PullData.checkPrice(self)
                        if test: correctCount += 1
                        else: incorrectCount += 1
                        if len(self.bandPrediction) == 15: break
                    if correctCount > incorrectCount:
                        self.scoreList[position] = "True"
                        self.bandPredictionResult = "Accurate"
                    else:
                        self.scoreList[position] = "False"
                        self.bandPredictionResult = "Inaccurate"
                
            self.seenDates = set()
            correctCount = 0
            incorrectCount = 0
            if indicator == 1:
                if self.position == 1:
                    for check in range(10):
                        rand = randint(0,len(self.HistoricalInfo))-2
                        self.guessDate = self.randDates[rand]
                        self.checkDate = self.randDates[rand+1]
                        test = PullData.upwardMomentum(self) == PullData.checkPrice(self)
                        if test: correctCount += 1
                        else: incorrectCount += 1
                        if len(self.momentumPrediction) == 15: break
                    if correctCount > incorrectCount:
                        self.scoreList[position] = "True"
                        self.momentumPredictionResult = "Accurate"
                    else:
                        self.scoreList[position] = "False"
                        self.momentumPredictionResult = "Inaccurate"
                        

            self.seenDates = set()
            correctCount = 0
            incorrectCount = 0
            if indicator == 1:
                if self.position == 2:
                    for check in range(10):
                        rand = randint(0,len(self.HistoricalInfo))-2
                        self.guessDate = self.randDates[rand]
                        self.checkDate = self.randDates[rand+1]
                        test = PullData.test10MVA(self, self.guessDate) == PullData.checkPrice(self)
                        if test: correctCount += 1
                        else: incorrectCount += 1
                        #if len(self.MVAPrediction) == 15: break
                    if correctCount > incorrectCount:
                        self.scoreList[position] = "True"
                        self.MVAPredictionResult = "Accurate"
                    else:
                        self.scoreList[position] = "False"
                        self.MVAPredictionResult = "Inaccurate"
                        
            self.position += 1
        effectiveness = (self.scoreList.count("True")/len(self.scoreList))
        return effectiveness

    def checkPrice(self): #Get actual price and compare to guess
        if self.position == 0:
            if self.HistoricalInfo[self.checkDate]['Close'] > self.HistoricalInfo[self.guessDate]['Close']:
                self.actualBandEvent += [(self.checkDate, "Up")]
                return "Up"
            self.actualBandEvent += [(self.checkDate, "Down")]
            return "Down"
        if self.position == 1:
            if self.HistoricalInfo[self.checkDate]['Close'] > self.HistoricalInfo[self.guessDate]['Close']:
                self.actualMomentumEvent += [(self.checkDate, "Up")]
                return "Up"
            self.actualMomentumEvent += [(self.checkDate, "Down")]
            return "Down"
        if self.position == 2:
            if self.HistoricalInfo[self.checkDate]['Close'] > self.HistoricalInfo[self.guessDate]['Close']:
                self.actualMVAEvent += [(self.checkDate, "Up")]
                return "Up"
            self.actualMVAEvent += [(self.checkDate, "Down")]
            return "Down"

    def predictTomorrow(self, bestIndicators):
        position = 0
        currentTest = []
        self.guessDate = self.endDate #current date
        if self.guessDate not in self.HistoricalInfo:
            self.guessDate = PullData.convertDate(self, 1, self.guessDate)
            if self.guessDate not in self.HistoricalInfo:
                self.guessDate = PullData.convertDate(self, 1, self.guessDate) 
        for indicator in bestIndicators:
            if indicator == 1:
                if position == 0:
                    MA10 = PullData.findNthDayMVAFromNDaysAgo(self, 10, self.guessDate)
                    self.guessPrice = self.HistoricalInfo[self.guessDate]['Close']
                    print("date, price: ", self.guessDate, self.guessPrice)
                    if (float(self.guessPrice) > 1.05*(MA10) or float(self.guessPrice) < .95*(MA10)):
                        if float(self.guessPrice) > 1.05*(MA10):
                            currentTest += ["Down"]
                        else:
                            currentTest += ["Up"]
                    else:
                        currentTest += ["None"]
                if position == 1:
                    MA20 = PullData.findNthDayMVAFromNDaysAgo(self, 20, self.guessDate)
                    MA40 = PullData.findNthDayMVAFromNDaysAgo(self, 40, self.guessDate)
                    if MA20 > MA40:
                        currentTest += ["Up"]
                    else:
                        currentTest += ["Down"]
                if position == 2:
                    MA10 = PullData.findNthDayMVAFromNDaysAgo(self, 10, self.guessDate)
                    self.guessPrice = float(self.HistoricalInfo[self.guessDate]['Close'])
                    if self.guessPrice > MA10:
                        currentTest += ["Up"]
                    else:
                        currentTest += ["Down"]
        if currentTest.count("Up") > currentTest.count("Down"):
            self.prediction = "Up"
            return self.prediction
        self.prediction = "Down"
        print(self.prediction)
        return self.prediction

    def runAutomation(self, iterations):
        effectiveness = 0
        for i in range(self.iterations):
            currentIndicatorTest = [randint(0,1) for j in range(len(self.indicators))]
            #currentIndicatorTest = [1,1,1]
            print(currentIndicatorTest)
            effectiveness = PullData.guessPrice(self, currentIndicatorTest)
            if effectiveness > self.bestIndicators[0]:
                self.bestIndicators = effectiveness, currentIndicatorTest
        return PullData.predictTomorrow(self, self.bestIndicators[1])

    def returnPrediction(self):
        print(self.prediction)
        return self.prediction
    
###############################################################################
#Animations
###############################################################################

def init(data):
    # load data.xyz as appropriate
    data.stockData = PullData()

    data.stock = (data.stockData.getStock())
    data.showDataButton = (750,100,850,175)
    data.showDataButtonMode = False

    data.predictButton = (750,200,850,275)
    data.predictButtonMode = False

    data.searchStockButton = (725,25,825,75)
    data.searchStockButtonMode = False    
    data.typedStockString = ""

    data.setCurrentDateButton = (750,325,850,350)
    data.setCurrentDateButtonMode = False
    data.typedCurrentDateString = ""

    data.setStartDateButton = (750,400,850,425)
    data.setStartDateButtonMode = False
    data.typedStartDateString = ""

    data.showGraphButton = (750,500,850,550)
    data.showGraphButtonMode = False

    data.automateButton = (750,600,850,625)
    data.automateButtonMode = False
    data.typedIterationsString = ""


    data.sampleStock1Mode = False
    data.sampleStock1 = (75,25,175,75)
    data.sampleStock2Mode = False
    data.sampleStock2 = (225,25,325,75)
    data.sampleStock3Mode = False
    data.sampleStock3 = (375,25,475,75)
    data.sampleStock4Mode = False
    data.sampleStock4 = (525,25,625,75)

    data.HistoricalInfo = None
    data.price = data.stockData.getPrice()
    data.prevClose = data.stockData.getPrevClose()
    data.percentChange = (float(data.stockData.getChange())/(float(data.price)-float(data.stockData.getChange())))*100
    data.percentChange = round(data.percentChange,3)
    data.date = data.stockData.getDate()

    data.bandPrediction = data.stockData.return10BandsData()
    data.actualBandEvent = data.stockData.returnActualBandEvent()
    data.bandPredictionResult = data.stockData.return10BandsPredictionResult()
    data.indicatorCount = 0

    data.momentumPrediction = data.stockData.returnMomentumData()
    data.actualMomentumEvent = data.stockData.returnActualMomentumData()

    data.MVAPrediction = data.stockData.returnMVAData()
    data.actualMVAEvent = data.stockData.returnActualMVAData()
    data.prediction = data.stockData.returnPrediction()
    data.splashMode = True


################################
#### Mode Dispatcher
################################
def mousePressed(event,data):

    if data.splashMode == True: 
        splashScreenMousePressed(event, data)
    else:
        mousePressed1(event,data)

def keyPressed(event,data):
    if data.splashMode == True: 
        splashScreenKeyPressed(event, data)
    else:
        keyPressed1(event, data)

def timerFired(data):
    if data.splashMode == True: 
        splashScreenTimerFired(data)
    else:
        timerFired1(data)

def redrawAll(canvas, data):
    if data.splashMode == True: 
        splashScreenRedrawAll(canvas, data)
    else:
        redrawAll1(canvas, data)



################################
#### Splashsauce
################################
def splashScreenMousePressed(event, data):
    if event.x < data.width and event.y < data.height:
        data.splashMode = False

def splashScreenKeyPressed(event, data):pass

def splashScreenTimerFired(data):pass

def splashScreenRedrawAll(canvas, data):
    canvas.create_rectangle(0,0,data.width,data.height, fill = "lime green")
    canvas.create_text(data.width/2, data.height/3, text = "STOCK PREDATOR", font = "TimesNewRoman 50")
    canvas.create_text(data.width/2, data.height/2, text = "Click Anywhere to Begin!", font = "TimesNewRoman 30")

################################



def mousePressed1(event, data):
    x,y = event.x, event.y
    predictButtonCall(data,x,y)
    showDataButtonCall(data,x,y)
    sampleStockSelector(data,x,y)
    searchStockCall(data,x,y)
    setCurrentDate(data,x,y)
    setStartDate(data,x,y)
    showGraphButtonCall(data,x,y)
    automateButtonCall(data,x,y)

def sampleStockSelector(data,x,y):
    if 75< x <175 and 25< y <75:
        data.stock = data.stockData.switchStocks()[0]
        data.stockData.setStock(data.stock)
        if data.sampleStock1Mode == False:
            data.sampleStock1Mode = True
            data.sampleStock2Mode = data.sampleStock3Mode = data.sampleStock4Mode = False
        else: data.sampleStock1Mode = False
        #init(data)
    elif 225< x <325 and 25< y <75:
        data.stock = data.stockData.switchStocks()[1]
        data.stockData.setStock(data.stock)
        if data.sampleStock2Mode == False:
            data.sampleStock2Mode = True
            data.sampleStock1Mode = data.sampleStock3Mode = data.sampleStock4Mode = False
        else: data.sampleStock2Mode = False
        #init(data)
    elif 375< x <475 and 25< y <75:
        data.stock = data.stockData.switchStocks()[2]
        data.stockData.setStock(data.stock)
        if data.sampleStock3Mode == False:
            data.sampleStock3Mode = True
            data.sampleStock1Mode = data.sampleStock2Mode = data.sampleStock4Mode = False
        else: data.sampleStock3Mode = False
        # init(data)
    elif 525< x <625 and 25< y <75:
        data.stock = data.stockData.switchStocks()[3]
        data.stockData.setStock(data.stock)
        if data.sampleStock4Mode == False:
            data.sampleStock4Mode = True
            data.sampleStock1Mode = data.sampleStock2Mode = data.sampleStock3Mode = False
        else: data.sampleStock4Mode = False
        # init(data)

    print(data.stock)

def predictButtonCall(data,x,y):
    if x > data.predictButton[0] and x < data.predictButton[2] and y > data.predictButton[1] and y < data.predictButton[3]:
        if data.predictButtonMode == False:
            data.predictButtonMode = True
        else:
            data.indicatorCount = 0
            data.predictButtonMode = False



def showDataButtonCall(data, x, y):
    if x > data.showDataButton[0] and x < data.showDataButton[2] and y > data.showDataButton[1] and y < data.showDataButton[3]:
        if data.showDataButtonMode == False:
            data.showDataButtonMode = True
        else:
            data.indicatorCount = 0
            data.showDataButtonMode = False

def searchStockCall(data,x,y):
    if x > data.searchStockButton[0] and x < data.searchStockButton[2] and y > data.searchStockButton[1] and y < data.searchStockButton[3]:
        if data.searchStockButtonMode == False:
            data.searchStockButtonMode = True
            data.typedStockString = ""
        else:
            data.searchStockButtonMode = False

def setCurrentDate(data,x,y):
    if x > data.setCurrentDateButton[0] and x < data.setCurrentDateButton[2] and y > data.setCurrentDateButton[1] and y < data.setCurrentDateButton[3]:
        if data.setCurrentDateButtonMode == False:
            data.setCurrentDateButtonMode = True
            data.typedCurrentDateString = ""
        else:
            data.setCurrentDateButtonMode = False

def setStartDate(data,x,y):
    if x > data.setStartDateButton[0] and x < data.setStartDateButton[2] and y > data.setStartDateButton[1] and y < data.setStartDateButton[3]:
        if data.setStartDateButtonMode == False:
            data.setStartDateButtonMode = True
            data.typedStartDateString = ""
        else:
            data.setStartDateButtonMode = False

def showGraphButtonCall(data,x,y):
    if x > data.showGraphButton[0] and x < data.showGraphButton[2] and y > data.showGraphButton[1] and y < data.showGraphButton[3]:
        if data.showGraphButtonMode == False:
            data.showGraphButtonMode = True
            data.stockData.showGraph()
        else:
            data.showGraphButtonMode = False

def automateButtonCall(data,x,y):
    if x > data.automateButton[0] and x < data.automateButton[2] and y > data.automateButton[1] and y < data.automateButton[3]:
        if data.automateButtonMode == False:
            data.automateButtonMode = True
            data.typedIterationsString = ""
        else:
            data.automateButtonMode = False

def keyPressed1(event, data):
    # use event.char and event.keysym
    print(event.keysym)
    if event.keysym == "Escape":
        init(data)
    if data.searchStockButtonMode == True:
        if event.keysym == "Return":
            data.stock = data.typedStockString.upper()
            data.stockData.setStock(data.stock)
            data.searchStockButtonMode = False
            data.sampleStock1Mode = data.sampleStock2Mode = data.sampleStock3Mode = data.stockSample4Mode = False
            print(data.stock)
            data.typedStockString = ""
            print(data.typedStockString)
        if event.keysym == "BackSpace":
            data.typedStockString = data.typedStockString[:-1]
        else:
            data.typedStockString += event.keysym

    if data.setCurrentDateButtonMode == True:
        if event.keysym == "Return":
            data.stockData.setCurrentDate(data.typedCurrentDateString)
            data.setCurrentDateButtonMode = False
            print(data.typedCurrentDateString)
            print(data.typedCurrentDateString)
            print("current date", data.stockData.setCurrentDate(data.typedCurrentDateString))
            data.date = data.stockData.getDate()
        
            
        elif event.keysym == "BackSpace":
            data.typedCurrentDateString = data.typedCurrentDateString[:-1]
            if len(data.typedCurrentDateString) == 4 or len(data.typedCurrentDateString) == 7:
                data.typedCurrentDateString = data.typedCurrentDateString[:-2]
        else:
            data.typedCurrentDateString += event.keysym
        if len(data.typedCurrentDateString) == 4 or len(data.typedCurrentDateString) == 7:
            data.typedCurrentDateString += "-"

    if data.setStartDateButtonMode == True:
        if event.keysym == "Return":
            data.stockData.setStartDate(data.typedStartDateString)
            data.setStartDateButtonMode = False
            print(data.typedStartDateString)
        elif event.keysym == "BackSpace":
            data.typedStartDateString = data.typedStartDateString[:-1]
            if len(data.typedStartDateString) == 4 or len(data.typedStartDateString) == 7:
                data.typedStartDateString = data.typedStartDateString[:-2]
        else:
            data.typedStartDateString += event.keysym
        if len(data.typedStartDateString) == 4 or len(data.typedStartDateString) == 7:
            data.typedStartDateString += "-"

    if data.automateButtonMode == True:
        if event.keysym == "Return":
            data.stockData.setIterations(data.typedIterationsString)
            data.stockData.findBestIndicators()
            data.prediction = data.stockData.returnPrediction()
            data.automateButtonMode = False
            print(data.typedIterationsString)
        elif event.keysym == "BackSpace":
            data.typedIterationsString = data.typedIterationsString[:-1]
        else:
            data.typedIterationsString += event.keysym
        
def timerFired1(data):
    pass

def redrawAll1(canvas, data):
    # draw in canvas
    canvas.create_text(10,data.height-10, text = "Press 'Esc' to refresh", font = "TimesNewRoman 15", anchor = W)

    sampleStockPosition = 0
    if data.sampleStock1Mode == True:
        canvas.create_rectangle(data.sampleStock1, width = 3)
    if data.sampleStock2Mode == True:
        canvas.create_rectangle(data.sampleStock2, width = 3)
    if data.sampleStock3Mode == True:
        canvas.create_rectangle(data.sampleStock3, width = 3)
    if data.sampleStock4Mode == True:
        canvas.create_rectangle(data.sampleStock4, width = 3)

    for currStock in data.stockData.switchStocks():
        coords = (75 + 150*sampleStockPosition, 25, 175 + 150*sampleStockPosition, 75)
        stockTextX = (coords[0]+coords[2])/2
        stockTextY = (coords[1]+coords[3])/2
        canvas.create_rectangle(coords)
        canvas.create_text(stockTextX,stockTextY, text = currStock)
        sampleStockPosition += 1

    canvas.create_text(450,100, text = "Current Stock: " + str(data.stock))

    canvas.create_rectangle(data.showDataButton)
    showDataButtonTextX = (data.showDataButton[0]+data.showDataButton[2])/2
    showDataButtonTextY = (data.showDataButton[1]+data.showDataButton[3])/2
    canvas.create_text(showDataButtonTextX,showDataButtonTextY, text = "Show Data")
    if data.showDataButtonMode == True:
        data.predictButtonMode = data.showGraphButtonMode = False
        if data.indicatorCount == 0:
            data.price = data.stockData.getPrice()
            data.prevClose = data.stockData.getPrevClose()
            data.percentChange = (float(data.stockData.getChange())/(float(data.price)-float(data.stockData.getChange())))*100
            data.percentChange = round(data.percentChange,3)
            data.indicatorCount = 1

        canvas.create_rectangle(data.showDataButton, width = 3)
        canvas.create_text(200,150, text = "Price: " + data.price)
        canvas.create_text(200,170, text = "Previous Close: " + data.prevClose)
        canvas.create_text(200,190, text = "Percent Change: " + str(data.percentChange) + "%")
        HistoricalY = 225
        data.HistoricalInfo = data.stockData.getGraphHistorical()
        for date in reversed(sorted(data.HistoricalInfo)):
            if data.HistoricalInfo[date]['Close'] > data.HistoricalInfo[date]['Open']:
                color = "green"
            else:
                color = "red"
            text = ""
            for qual in ('Open', 'Close', 'High', 'Low'):
                text += qual + ": " + (data.HistoricalInfo[date][qual]) + " "
            canvas.create_text(25,HistoricalY, text = "("+date+") "+text, anchor = "w", fill = color)
            HistoricalY += 20

    canvas.create_rectangle(data.searchStockButton)
    searchStockButtonTextX = (data.searchStockButton[0]+data.searchStockButton[2])/2
    searchStockButtonTextY = (data.searchStockButton[1]+data.searchStockButton[3])/2
    canvas.create_text(searchStockButtonTextX-85, searchStockButtonTextY, text = "Search:")

    if data.searchStockButtonMode == True:
        canvas.create_rectangle(data.searchStockButton, width = 3)
        canvas.create_text(searchStockButtonTextX,searchStockButtonTextY, text = data.typedStockString)


    predictButtonTextX = (data.predictButton[0]+data.predictButton[2])/2
    predictButtonTextY = (data.predictButton[1]+data.predictButton[3])/2
    PredYPosition = 150
    ActYPosition = 160
    if data.predictButtonMode == True:
        data.showDataButtonMode = data.showGraphButtonMode = False
        canvas.create_rectangle(data.predictButton, width = 3)

    if data.predictButtonMode == True:
        data.showDataButtonMode = data.showGraphButtonMode = False
        if data.indicatorCount == 0: #Gets fresh data
            print("Here")
            data.stockData.findBestIndicators()
            data.bandPrediction = data.stockData.return10BandsData()
            data.actualBandEvent = data.stockData.returnActualBandEvent()

            data.momentumPrediction = data.stockData.returnMomentumData()
            data.actualMomentumEvent = data.stockData.returnActualMomentumData()

            data.MVAPrediction = data.stockData.returnMVAData()
            data.actualMVAEvent = data.stockData.returnActualMVAData()
            data.prediction = data.stockData.returnPrediction()
            data.indicatorCount = 1 #Stops getting fresh data


        count = 0
        if data.bandPrediction != [] and data.actualBandEvent != []:
            for position in range(len(data.bandPrediction)):
                if count == 15: break
                canvas.create_text(150, 125, text = "Bollinger Band Predictions: ", font = "TimesNewRoman 10")
                canvas.create_text(20, PredYPosition, text = data.bandPrediction[position][0] + "  Prediction: ",
                 anchor = "w", font = "TimesNewRoman 10")
                canvas.create_text(200, PredYPosition, text = data.bandPrediction[position][1],
                 fill = "green" if data.bandPrediction[position][1] == "Up" else "red", anchor = "w", font = "TimesNewRoman 10")
                canvas.create_text(20, ActYPosition, text = data.actualBandEvent[position][0] + "  Actual Event: ",
                 anchor = "w", font = "TimesNewRoman 10")
                canvas.create_text(200, ActYPosition, text = data.actualBandEvent[position][1],
                 fill = "green" if data.actualBandEvent[position][1] == "Up" else "red", anchor = "w", font = "TimesNewRoman 10")
                PredYPosition += 30
                ActYPosition += 30
                count += 1
            count = 0
            PredYPosition = 150
            ActYPosition = 160

        if data.momentumPrediction != [] and data.actualMomentumEvent != []:
            for position in range(len(data.momentumPrediction)):
                if count == 15: break
                canvas.create_text(350, 125, text = "Upward Momentum Predictions: ", font = "TimesNewRoman 10")
                canvas.create_text(250, PredYPosition, text = data.momentumPrediction[position][0] + "  Prediction: ",
                 anchor = "w", font = "TimesNewRoman 10")
                canvas.create_text(430, PredYPosition, text = data.momentumPrediction[position][1],
                 fill = "green" if data.momentumPrediction[position][1] == "Up" else "red", anchor = "w", font = "TimesNewRoman 10")
                canvas.create_text(250, ActYPosition, text = data.actualMomentumEvent[position][0] + "  Actual Event: ",
                 anchor = "w", font = "TimesNewRoman 10")
                canvas.create_text(430, ActYPosition, text = data.actualMomentumEvent[position][1],
                 fill = "green" if data.actualMomentumEvent[position][1] == "Up" else "red", anchor = "w", font = "TimesNewRoman 10")
                PredYPosition += 30
                ActYPosition += 30
                count += 1
            count = 0
            PredYPosition = 150
            ActYPosition = 160

        if data.MVAPrediction != [] and data.actualMVAEvent != []:
            for position in range(len(data.MVAPrediction)):
                if count == 15: break
                canvas.create_text(580, 125, text = "10 Day Moving Average Prediction: ", font = "TimesNewRoman 10")
                canvas.create_text(480, PredYPosition, text = data.MVAPrediction[position][0] + "  Prediction: ",
                 anchor = "w", font = "TimesNewRoman 10")
                canvas.create_text(660, PredYPosition, text = data.MVAPrediction[position][1],
                 fill = "green" if data.MVAPrediction[position][1] == "Up" else "red", anchor = "w", font = "TimesNewRoman 10")
                canvas.create_text(480, ActYPosition, text = data.actualMVAEvent[position][0] + "  Actual Event: ",
                 anchor = "w", font = "TimesNewRoman 10")
                canvas.create_text(660, ActYPosition, text = data.actualMVAEvent[position][1],
                 fill = "green" if data.actualMVAEvent[position][1] == "Up" else "red", anchor = "w", font = "TimesNewRoman 10")
                PredYPosition += 30
                ActYPosition += 30
                count += 1
            count = 0
            PredYPosition = 150
            ActYPosition = 160

        canvas.create_text(data.width/2,5*data.height/6,text = "Prediction on "+ data.date +": " +data.prediction,
            fill = "green" if data.prediction == "Up" else "red")

    canvas.create_rectangle(data.predictButton)
    canvas.create_text(predictButtonTextX,predictButtonTextY,text = "Predict")
    
    canvas.create_rectangle(data.showGraphButton)
    showGraphButtonX = (data.showGraphButton[0] + data.showGraphButton[2])/2
    showGraphButtonY = (data.showGraphButton[1] + data.showGraphButton[3])/2
    canvas.create_text(showGraphButtonX,showGraphButtonY, text = "Show Graph")
    if data.showGraphButtonMode == True:
        canvas.create_rectangle(data.showGraphButton, width = 3)



    canvas.create_rectangle(data.setCurrentDateButton)
    setCurrentDateButtonX = (data.setCurrentDateButton[0] + data.setCurrentDateButton[2])/2
    setCurrentDateButtonY = (data.setCurrentDateButton[1] + data.setCurrentDateButton[3])/2
    canvas.create_text(setCurrentDateButtonX,setCurrentDateButtonY-25, text = "Enter Current Date (yyyy-mm-dd):")
    canvas.create_text(setCurrentDateButtonX,setCurrentDateButtonY, text = data.typedCurrentDateString)
    
    if data.setCurrentDateButtonMode == True:
        canvas.create_rectangle(data.setCurrentDateButton, width = 3)
        canvas.create_text(setCurrentDateButtonX,setCurrentDateButtonY, text = data.typedCurrentDateString)
    
    canvas.create_rectangle(data.setStartDateButton)
    setStartDateButtonX = (data.setStartDateButton[0] + data.setStartDateButton[2])/2
    setStartDateButtonY = (data.setStartDateButton[1] + data.setStartDateButton[3])/2
    canvas.create_text(setStartDateButtonX,setStartDateButtonY-25, text = "Enter Start Date (yyyy-mm-dd):")
    canvas.create_text(setStartDateButtonX,setStartDateButtonY, text = data.typedStartDateString)
    
    if data.setStartDateButtonMode == True:
        canvas.create_rectangle(data.setStartDateButton, width = 3)
        canvas.create_text(setStartDateButtonX,setStartDateButtonY, text = data.typedStartDateString)
    

    canvas.create_rectangle(data.automateButton)
    automateTextX = (data.automateButton[0] + data.automateButton[2])/2
    automateTextY = (data.automateButton[1] + data.automateButton[3])/2
    canvas.create_text(automateTextX,automateTextY-25, text = "Automate with 'n' Iterations: ")
    canvas.create_text(automateTextX,automateTextY, text = data.typedIterationsString)
    if data.automateButtonMode == True:
        canvas.create_rectangle(data.automateButton, width = 3)
        canvas.create_text(automateTextX,automateTextY, text = data.typedIterationsString)
####################################
# use the run function as-is
####################################

def run(width=900, height=900):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        redrawAll(canvas, data)
        canvas.update()    

    def mousePressedWrapper(event, canvas, data):
        mousePressed(event, data)
        redrawAllWrapper(canvas, data)

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timerDelay = 100 # milliseconds
    init(data)
    # create the root and the canvas
    root = Tk()

    canvas = Canvas(root, width=data.width, height=data.height)

    canvas.pack()
    # set up events
    root.bind("<Button-1>", lambda event:
                            mousePressedWrapper(event, canvas, data))
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    timerFiredWrapper(canvas, data)
    # and launch the app
    #root.mainloop()  # blocks until window is closed
    print("bye!")


run(900, 800)



