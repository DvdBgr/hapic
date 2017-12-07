# -*- coding: utf-8 -*-
import json
from http import HTTPStatus

import bottle
import time
from datetime import datetime
import hapic
from example.fake_api.schema import *
from hapic.data import HapicData


class NoContentException(Exception):
    pass


class BottleController(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutResponseSchema())
    def about(self):
        """
        General information about this API.
        """
        return {
            'version': '1.2.3',
            'datetime': datetime(2017, 12, 7, 10, 55, 8, 488996),
        }

    @hapic.with_api_doc()
    @hapic.output_body(ListsUserSchema())
    def get_users(self):
        """
        Obtain users list.
        """
        return {
            'item_nb': 1,
            'items': [
                {
                    'id': 4,
                    'username': 'some_user',
                    'display_name': 'Damien Accorsi',
                    'company': 'Algoo',
                },
            ],
            'pagination': {
                'first_id': 0,
                'last_id': 5,
                'current_id': 0,
            }
        }

    @hapic.with_api_doc()
    @hapic.input_path(UserPathSchema())
    @hapic.output_body(UserSchema())
    def get_user(self, id, hapic_data: HapicData):
        """
        Obtain one user
        """
        return {
             'id': 4,
             'username': 'some_user',
             'email_address': 'some.user@hapic.com',
             'first_name': 'Damien',
             'last_name': 'Accorsi',
             'display_name': 'Damien Accorsi',
             'company': 'Algoo',
        }

    @hapic.with_api_doc()
    # TODO - G.M - 2017-12-5 - Support input_forms ?
    # TODO - G.M - 2017-12-5 - Support exclude, only ?
    @hapic.input_body(UserSchema(exclude=('id',)))
    @hapic.output_body(UserSchema())
    def add_user(self, hapic_data: HapicData):
        """
        Add new user
        """
        return {
             'id': 4,
             'username': 'some_user',
             'email_address': 'some.user@hapic.com',
             'first_name': 'Damien',
             'last_name': 'Accorsi',
             'display_name': 'Damien Accorsi',
             'company': 'Algoo',
        }

    @hapic.with_api_doc()
    @hapic.handle_exception(NoContentException, http_code=HTTPStatus.NO_CONTENT)
    @hapic.input_path(UserPathSchema())
    def del_user(self, id, hapic_data: HapicData):
        """
        delete user
        """

        # TODO - G.M - 2017-12-05 - Add better
        #  way to doc response of this function, using response object ?
        # return bottle.Response(
        #     status=204,
        # )
        raise NoContentException

    def bind(self, app:bottle.Bottle):
        app.route('/about', callback=self.about)
        app.route('/users', callback=self.get_users)
        app.route('/users/<id>', callback=self.get_user)
        app.route('/users/', callback=self.add_user,  method='POST')
        app.route('/users/<id>', callback=self.del_user, method='DELETE')

if __name__ == "__main__":
    app = bottle.Bottle()
    controllers = BottleController()
    controllers.bind(app)
    hapic.set_context(hapic.ext.bottle.BottleContext(app))
    time.sleep(1)
    s = json.dumps(hapic.generate_doc())
    time.sleep(1)
    # print swagger doc
    print(s)
    # Run app
    app.run(host='localhost', port=8081, debug=True)
