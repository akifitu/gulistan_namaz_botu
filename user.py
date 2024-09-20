from datetime import datetime
from typing import Dict

# 7321495529:AAGuB45qmPioQO9gO5LIFgwdlRCW8qzBvlo
class User:
    def __init__(self, name, totalScore, days):
        self.name = name
        self.totalScore = totalScore
        self.days = days

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name

    def getTotalScore(self):
        return self.totalScore

    def setTotalScore(self, totalScore):
        self.totalScore = totalScore

    def addDay(self, dateString: str, score: int) -> None:
        date = datetime.strptime(dateString, '%d.%m.%Y')
        if date in self.days:
            self.totalScore -= self.days[date]  # Subtract the old score
        self.days[date] = score
        self.totalScore += score  # Add the new score
        print(f" score: {score}, totalscore: {self.totalScore}")

    def __repr__(self):
        return f"User(name={self.name}, totalScore={self.totalScore}, days={self.days})"
