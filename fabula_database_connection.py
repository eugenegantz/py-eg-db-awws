""" Fabula (AwwS) database connection module """

import re
import json
import typing
import datetime
import http.client
import urllib.parse
from .base_64 import encode as base_64_encode
from .fabula_database_response import FabulaDatabaseResponse


class FabulaDatabaseConnection:

	token: typing.Dict = None


	db_server_url: typing.AnyStr = ''


	db_login_hash: typing.AnyStr = ''


	db_login: typing.AnyStr = ''


	db_login_2: typing.AnyStr = ''


	db_name: typing.AnyStr = ''


	db_src: typing.AnyStr = ''


	def __init__(
		self,
		db_server_url,
		db_name,
		db_src,
		db_login_hash,
		db_login,
		db_login_2,
	):
		self.db_server_url  = db_server_url
		self.db_src         = db_src
		self.db_name        = db_name

		self.db_login       = db_login
		self.db_login_2     = db_login_2
		self.db_login_hash  = db_login_hash


	def __encode_fields(
		self,
		fields          : typing.Dict[str, str],
		request_method  : typing.AnyStr,
	):
		""" create request string """

		sep = ','
		encoded_string = []
		request_method = request_method.upper()

		for k in fields:
			encoded_string.append(k + ':"' + fields[k] + '"')

		encoded_string = "{" + sep.join(encoded_string) + "}"

		if 'GET' == request_method:
			encoded_string = base_64_encode(encoded_string)

		return encoded_string


	def __encode_login(
		self,
		tm              : typing.AnyStr,
		db_name         : typing.AnyStr,
		login           : typing.AnyStr,
		login2          : typing.AnyStr,
		login_hash      : typing.AnyStr,
		login_origin    : typing.AnyStr,
		request_method  : typing.AnyStr,
	):
		""" create login query string """

		# example:
		# {Src: 'master', Sql: 'Auth', Alias: 'Auth', Conf: 'acme', Login: 'john', Login2: 'john', Sha1: 'c5d9...', Tm: '04:20', Origin: 'http://localhost.ru'}

		fields = {
			'Src'       : 'main',
			'Sql'       : 'Auth',
			'Alias'     : 'Auth',
			'Conf'      : db_name,
			'Login'     : login,
			'Login2'    : login2,
			'Sha1'      : login_hash,
			'Tm'        : tm,
			'Origin'    : login_origin,
		}

		return self.__encode_fields(fields, request_method)


	def __encode_query(
		self,
		token_object    : typing.Dict,
		request_method  : typing.AnyStr,
		db_name         : typing.AnyStr,
		db_src          : typing.AnyStr,
		query           : typing.AnyStr,
		props           : typing.Dict[str, str] = None,
		db_cache        = ''
	):
		""" create query string """

		# example:
		# {Conf: "acme", Src: "*master", Cache: "req_id", Sql: "UU0...", IDS: "594...", User: "541", Rights: "", Login: ""}

		fields = {
			'id'    : '0',
			'Conf'  : db_name,
			'Src'   : db_src,
			'Login' : '',
			'Pwd'   : '',
			'Cache' : base_64_encode(db_cache),
			'Sql'   : base_64_encode(query),
			'IDS'   : token_object.get('IDS', ''),
			'User'  : token_object.get('User', ''),
		}

		fields.update(props or {})

		return self.__encode_fields(fields, request_method)


	def __validate_token(self, token: typing.Optional[typing.Dict] = None) -> bool:
		# 'Err': '',
		# 'User': '541',
		# 'Login': 'john',
		# 'dbName': 'acme',
		# 'sqlType': 'postgres',
		# 'Rights': '',
		# 'Ok': 1,
		# 'IDS': '594...',
		# 'Sha1': 'c5d9...',
		# 'timestamp': 1602626517

		if token is None:
			return False

		if token.get('Err'):
			return False

		if token.get('IDS') is None:
			return False

		# TODO validate timestamp: should be today's (token is invalidated every night at 00:00)

		return True


	def login(self, token = None):
		""" auth in database and get secure token """

		if self.__validate_token(token) is True:
			self.token = token

		db_url              = self.db_server_url.strip('\\/')
		db_url_parsed       = urllib.parse.urlparse(db_url)

		db_origin_url       = self.db_server_url.strip('\\/')

		db_host, _, db_port = db_url_parsed.netloc.partition(':')
		db_port             = db_port or None

		request_method      = 'GET'

		now                 = datetime.datetime.now()
		tm                  = now.strftime('%H:%M')

		body = self.__encode_login(
			tm              = tm,
			db_name         = self.db_name,
			login           = self.db_login,
			login2          = self.db_login_2,
			login_hash      = self.db_login_hash,
			login_origin    = db_origin_url,
			request_method  = request_method
		)

		db_url_path = '/login?' + body

		req = http.client.HTTPConnection(db_host, db_port)
		req.request(method=request_method, url=db_url_path)

		res = req.getresponse()

		res_str = res.read().decode('cp1251')
		res_str = re.sub(r"[']", '"', res_str)

		self.token = json.loads(res_str)
		self.token['timestamp'] = datetime.datetime.now().timestamp()

		return self.token


	def query(
		self,
		query       : typing.AnyStr,
		db_cache    : typing.AnyStr = '*___'
	):
		""" request query to awws database. return data from database """

		request_method      = 'POST'

		db_url              = self.db_server_url.strip('\\/')
		db_url_parsed       = urllib.parse.urlparse(db_url)
		db_url_path         = '/db?'

		db_host, _, db_port = db_url_parsed.netloc.partition(':')
		db_port             = db_port or None

		body = self.__encode_query(
			token_object    = self.token,
			db_src          = self.db_src,
			db_name         = self.db_name,
			db_cache        = db_cache,
			request_method  = request_method,
			query           = query,
		)

		req = http.client.HTTPConnection(db_host, db_port)
		req.request(method=request_method, url=db_url_path, body=body)

		res                 = req.getresponse()
		res_str             = res.read().decode('cp1251')

		db_res              = json.loads(res_str)

		return FabulaDatabaseResponse(db_res)
