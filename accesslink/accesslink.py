#!/usr/bin/env python

from . import endpoints
from .oauth2 import OAuth2Client
import datetime

AUTHORIZATION_URL = "https://flow.polar.com/oauth2/authorization"
ACCESS_TOKEN_URL = "https://polarremote.com/v2/oauth2/token"
ACCESSLINK_URL = "https://www.polaraccesslink.com/v3"


class AccessLink(object):
    """Wrapper class for Polar Open AccessLink API v3"""

    def __init__(self, client_id, client_secret, redirect_url=None):
        if not client_id or not client_secret:
            raise ValueError("Client id and secret must be provided.")

        self.oauth = OAuth2Client(url=ACCESSLINK_URL,
                                  authorization_url=AUTHORIZATION_URL,
                                  access_token_url=ACCESS_TOKEN_URL,
                                  redirect_url=redirect_url,
                                  client_id=client_id,
                                  client_secret=client_secret)

        self.users = endpoints.Users(oauth=self.oauth)
        self.pull_notifications = endpoints.PullNotifications(oauth=self.oauth)
        self.training_data = endpoints.TrainingData(oauth=self.oauth)
        self.physical_info = endpoints.PhysicalInfo(oauth=self.oauth)
        self.daily_activity = endpoints.DailyActivity(oauth=self.oauth)
        self.continuous_heart_rate = endpoints.ContinuousHeartRate(oauth=self.oauth)

    @property
    def authorization_url(self):
        """Get the authorization url for the client"""
        return self.oauth.get_authorization_url()

    def get_access_token(self, authorization_code):
        """Request access token for a user.

        :param authorization_code: authorization code received from authorization endpoint.
        """
        return self.oauth.get_access_token(authorization_code)

    def get_exercises(self, access_token):
        return self.oauth.get(endpoint="/exercises", access_token=access_token)

    def get_sleep(self, access_token):
        # Existing api call is kinda b0rked, only returns last 28 days. We're gonna walk the entire period manually.
        start_date = datetime.date(2023, 6, 20)
        end_date = datetime.date.today()
        delta = datetime.timedelta(days=1)
        sleep_data = {"nights": []}
        while start_date <= end_date:
            print ("   attempt fetch {}".format(start_date.strftime("%Y-%m-%d")))
            try:
                night_data = self.oauth.get(endpoint="/users/sleep/{}".format(start_date.strftime("%Y-%m-%d")), access_token=access_token)
                sleep_data["nights"].append(night_data)
            except:
                pass
            start_date += delta

        return sleep_data
    
#    def get_sleep(self, access_token):
#        return self.oauth.get(endpoint="/users/sleep/", access_token=access_token)
    
    def get_recharge(self, access_token):
        return self.oauth.get(endpoint="/users/nightly-recharge/", access_token=access_token)

    def get_userdata(self, user_id,access_token):
        return self.oauth.get(endpoint="/users/"+ str(user_id), access_token= access_token)

    def get_continuous_heart_rate(self, access_token, start_date, end_date):
        # This API call is ALSO quite silly. It only allows us to pull 28 days at a time, which is indeed very silly.
        # If there are more than 28 days, we need to parse this out into days
        heart_data = {"heart_rates": []}
        delta = datetime.timedelta(days=24)
        while start_date <= end_date:
            #fetch some data
            month_data = self.oauth.get(endpoint="/users/continuous-heart-rate/?from={}&to={}".format(start_date.strftime("%Y-%m-%d"), (start_date+delta).strftime("%Y-%m-%d")), access_token=access_token)
            heart_data["heart_rates"] = heart_data["heart_rates"] + month_data["heart_rates"]
            start_date += delta

        return heart_data
#        return self.oauth.get(endpoint="/users/continuous-heart-rate/?from={}&to={}".format(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")), access_token=access_token)
#        return self.oauth.get(endpoint="/users/continuous-heart-rate/?from=2023-05-20&to=2023-06-15", access_token=access_token)
