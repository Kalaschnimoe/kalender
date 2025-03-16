"""
Diese Klasse beinhaltet folgende Funktionen:
    connectToDatabase: verbindet sich zur übergebenen Datenbank
    requestData: gibt die angefragten Datenbankinhalte zurück
    closeDatabaseConnection: schließt die Datenbankverbindung
    getSQLString: setzt den SQLString zusammen und gibt ihn zurück


Folgende Parameter sind notwendig:
    - Datenbankname
    - Tabellenname (Login)
    - gesuchte Spalte(n) (passwort)
    - gesuchter Wert (pw)
    - angeforderter Wert (*)
    Bsp: SELECT * FROM Login WHERE passwort LIKE pw

"""

import pymysql


class Database():
    def __init__(self, ):
        self.__database = 'd034da83'
        self.__password = 'pMFLJ2Rvd9SosCZ9'
        self.__IP = '85.13.129.129'

    def connectToDatabase(self):
        try:
            self.__connection = pymysql.connect(user=self.__database, passwd=self.__password, host=self.__IP,
                                                database=self.__database)
            self.__cursor = self.__connection.cursor()
            return True
        except Exception as ex:
            return False

    def closeDatabaseConnection(self):
        try:
            self.__cursor.close()
            self.__connection.close()
        except:
            pass

    def requestData(self, table, reqItem='*', param1="empty", value1="empty", param2="empty", value2="empty",
                    param3="empty", value3="empty"):
        sqlquery = self.__getSQLString(table, reqItem=reqItem, param1=param1, value1=value1, param2=param2,
                                       value2=value2,
                                       param3=param3, value3=value3)
        self.__cursor.execute(sqlquery)
        row = self.__cursor.fetchone()
        if row:
            return row
        else:
            raise LookupError

    def requestAllRowsInTable(self, table, reqItem='*', param1="empty", value1="empty", param2="empty", value2="empty",
                              param3="empty", value3="empty", sort=False, sort_direction="ASC", sort_param="ID"):

        if sort:
            sqlquery = self.__getSQLStringSorted(table, reqItem=reqItem, param1=param1, value1=value1, param2=param2,
                                                 value2=value2,
                                                 param3=param3, value3=value3, sort_direction=sort_direction,
                                                 sort_paramter=sort_param)
        else:
            sqlquery = self.__getSQLString(table, reqItem=reqItem, param1=param1, value1=value1, param2=param2,
                                           value2=value2,
                                           param3=param3, value3=value3)
        self.__cursor.execute(sqlquery)
        row = self.__cursor.fetchall()
        if row:
            return row
        else:
            raise LookupError

    def __getSQLString(self, table, reqItem, param1, value1, param2, value2, param3, value3):
        if reqItem != "'*'":
            reqItem = str(reqItem)

        if param1 == "empty":
            return f"SELECT {reqItem} FROM {str(table)}"
        elif param2 == "empty":
            return "SELECT {} FROM {} WHERE {} LIKE '{}' ".format(reqItem, table, param1, value1)
        elif param3 == "empty":
            return "SELECT {} FROM {} WHERE {} LIKE '{}' AND {} LIKE '{}' ".format(reqItem, table, param1, value1,
                                                                                   param2, value2)
        else:
            return "SELECT {} FROM {} WHERE {} LIKE '{}' AND {} LIKE '{}' AND {} LIKE '{}' ".format(reqItem, table,
                                                                                                    param1, value1,
                                                                                                    param2, value2,
                                                                                                    param3, value3)

    def __getSQLStringSorted(self, table, reqItem, param1, value1, param2, value2, param3, value3, sort_direction,
                             sort_paramter):
        if reqItem != "'*'":
            reqItem = str(reqItem)

        if param1 == "empty":
            return f"SELECT {reqItem} FROM {str(table)} ORDER BY `{table}`.`{sort_paramter}` {sort_direction}"
        elif param2 == "empty":
            return "SELECT {} FROM {} WHERE {} LIKE '{}' ORDER BY `{}`.`{}` {}".format(
                reqItem, table, param1, value1, table, sort_paramter, sort_direction)
        elif param3 == "empty":
            return "SELECT {} FROM {} WHERE {} LIKE '{}' AND {} LIKE '{}' ORDER BY `{}`.`{}` {}".format(reqItem, table,
                                                                                                        param1, value1,
                                                                                                        param2, value2,
                                                                                                        table,
                                                                                                        sort_paramter,
                                                                                                        sort_direction)
        else:
            return "SELECT {} FROM {} WHERE {} LIKE '{}' AND {} LIKE '{}' AND {} LIKE '{}' `{}`.`{}` {}".format(reqItem,
                                                                                                                table,
                                                                                                                param1,
                                                                                                                value1,
                                                                                                                param2,
                                                                                                                value2,
                                                                                                                param3,
                                                                                                                value3,
                                                                                                                table,
                                                                                                                sort_paramter,
                                                                                                                sort_direction)

    def createNewUser(self, username, device_id):
        sqlquery = "INSERT INTO `Login` (`ID`, `Benutzername`, `device_id`) VALUES ('NULL','{}','{}')".format(username,
                                                                                                              device_id)
        self.__cursor.execute(sqlquery)

    def updateDeviceID(self, username, device_id):
        sqlquery = "UPDATE `Login` SET `device_id` = '{}' WHERE `Login`.`Benutzername` = '{}'".format(device_id,
                                                                                                      username)
        self.__cursor.execute(sqlquery)

    def deleteDeviceID(self, device_id):
        sqlquery = "UPDATE `Login` SET `device_id` = '' WHERE `Login`.`device_id` = '{}'".format(device_id)
        self.__cursor.execute(sqlquery)

    def upload_vorlage(self, benutzer_id, benutzername, startzeitstunde, startzeitminute, endzeitstunde, endzeitminute,
                       dienstbezeichnung):
        sqlquery = "INSERT INTO `Vorlagen` (`ID`, `Benutzer_ID`, `Benutzername`, `Startzeith`, `Startzeitmin`, `Endzeith`, `Endzeitmin`, `Dienstbezeichnung`) " \
                   "VALUES ('NULL','{}','{}','{}','{}','{}','{}','{}')".format(
            benutzer_id,
            benutzername,
            startzeitstunde,
            startzeitminute,
            endzeitstunde,
            endzeitminute,
            dienstbezeichnung
        )

        self.__cursor.execute(sqlquery)

    def deleteVorlage(self, vorlagen_id):
        sqlquery = "DELETE FROM `Vorlagen` WHERE `Vorlagen`.`ID` = '{}'".format(vorlagen_id)
        self.__cursor.execute(sqlquery)

    def updateVorlage(self, startzeith, startzeitmin, endzeith, endzeitmin, vorlagen_id):
        sqlquery = "UPDATE `Vorlagen` SET `Startzeith` = '{}', `Startzeitmin` = '{}',`Endzeith` = '{}',`Endzeitmin` = '{}'  WHERE `Vorlagen`.`ID` = '{}'".format(
            startzeith, startzeitmin, endzeith, endzeitmin, vorlagen_id)
        self.__cursor.execute(sqlquery)

    def requestDienste(self, lastyear, nextyear):
        sqlquery = "SELECT * FROM `Dienste` WHERE `Jahr` >= '{}' AND `Jahr` <= '{}' ORDER BY `Jahr` ASC, `Monat` ASC, `Tag` ASC".format(
            lastyear, nextyear)
        self.__cursor.execute(sqlquery)
        row = self.__cursor.fetchall()
        return row

    def uploadDienst(self, benutzer_id, benutzername, jahr, monat, tag, startzeitstunde, startzeitminute, endzeitstunde,
                     endzeitminute,
                     dienstbezeichnung):
        sqlquery = "INSERT INTO `Dienste` (`ID`, `Benutzer_ID`, `Benutzername`, `Jahr`, `Monat`, `Tag`, `Startzeith`, `Startzeitmin`, `Endzeith`, `Endzeitmin`, `Dienstname`) " \
                   "VALUES ('NULL','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
            benutzer_id,
            benutzername,
            jahr,
            monat,
            tag,
            startzeitstunde,
            startzeitminute,
            endzeitstunde,
            endzeitminute,
            dienstbezeichnung
        )

        self.__cursor.execute(sqlquery)

    def deleteDienst(self, dienst_id):
        sqlquery = "DELETE FROM `Dienste` WHERE `Dienste`.`ID` = '{}'".format(dienst_id)
        self.__cursor.execute(sqlquery)

if __name__ == '__main__':
    db = Database()
    print(db.requestData(table="d034da83", param1="test", value1="test2"))
