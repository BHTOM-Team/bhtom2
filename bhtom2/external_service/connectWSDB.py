import psycopg2
from bhtom2 import settings
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom2.exceptions.external_service import InvalidExternalServiceStatusException

        # wsdbconn_string = "host=cappc127.ast.cam.ac.uk port=5432 dbname=wsdb user="+WSDB_USER+" password="+WSDB_PASSWORD
        # wsdbconn = psycopg2.connect(wsdbconn_string)
        # wsdbcur = wsdbconn.cursor()

class WSDBConnection():
    def __init__(self):
        self.__logger = BHTOMLogger(__name__, 'Bhtom: WSDB Connection')
    
    @property
    def logger(self):
        return self.__logger


#connects, runs the query and closes the connection
    def run_query(self, query: str):
        try:
            self.__connection = psycopg2.connect(
            host=settings.WSDB_HOST,
            dbname='wsdb',
            user=settings.WSDB_USER,
            port=settings.WSDB_PORT,
            password=settings.WSDB_PASSWORD)
            self.__cursor = self.__connection.cursor()
        except Exception as e:
            self.__logger.error(f'Error while connecting to WSDB: {e}')
            raise InvalidExternalServiceStatusException('Can\'t connect to WSDB')

        self.__cursor.execute(query)
        result= self.__cursor.fetchall()
        self.__connection.close()
        return result
