#!/usr/bin/env python

from .resource import Resource
from .continuous_heart_rate_transaction import ContinuousHeartRateTransaction


class ContinuousHeartRate(Resource):
    """This resource allows partners to access their users' continuous heartrate

    https://www.polar.com/accesslink-api/?http#daily-activity
    """
    def create_transaction(self, user_id, access_token):
        print("henlo i am heart rate query {}, {}".format(user_id, access_token))
        """Initiate daily activity transaction

        Check for new daily activity and create a new transaction if data is available.

        :param user_id: id of the user
        :param access_token: access token of the user
        """
        response = self._post(endpoint="/users/continuous-heart-rate?from=2023-01-01&to=2024-01-01",
                              access_token=access_token)
        if not response:
            return None

        return DailyActivityTransaction(oauth=self.oauth,
                                        transaction_url=response["resource-uri"],
                                        user_id=user_id,
                                        access_token=access_token)
