"""
    Database helpers
        
    Created on 2010-08-19
    @author: jldupont
"""
import copy
import os
import sqlite3

__all__=["dbHelper"]

class DbHelper(object):
    
    def __init__(self, dbpath, table_name, table_params):
        self.dbpath=dbpath
        self.table_name=table_name
        self.table_params=table_params
        self.fields=[]
        self.emptyDicTemplate={}
        
        self.path=os.path.expanduser(self.dbpath)
        self.conn=sqlite3.connect(self.path, check_same_thread=False)
        self.c = self.conn.cursor()

        self._prepare()
        self._prepareEmptyDict()
        self._executeCreate()
        

    CREATE_STATEMENT_TEMPLATE="""create table if not exists %(table)s ( %(columns)s )"""
    def _prepare(self):
        """
        - Prepares the "create" statement
        - Prepars the "fields" list
        """
        cols=""
        for entry in self.table_params:
            col_name, col_type=entry
            
            ## order is critical!
            self.fields.append(col_name)            
            cols += "%s %s," % (col_name, col_type)
        cols=cols.rstrip(",")
        
        self.create_statement = self.CREATE_STATEMENT_TEMPLATE % ({"table":self.table_name, "columns": cols})
        
    def _executeCreate(self):
        self.c.execute(self.create_statement)
        
    def makeDict(self, ituple):
        if ituple is None:
            return {}
        dic={}
        index=0
        for el in ituple:
            key=self.fields[index]
            dic[key]=el
            index += 1
        return dic
        
    def makeEmptyDict(self):
        return copy.deepcopy(self.emptyDicTemplate)
        
    def _prepareEmptyDict(self):
        """ Prepares an empty result dictionary
        """
        for col_name, col_type in self.table_params:
            if col_type=="text":
                self.emptyDicTemplate[col_name]=""
            else:
                if col_type=="integer":
                    self.emptyDicTemplate[col_name]=0
                else:
                    if col_type=="float":
                        self.emptyDicTemplate[col_name]=0.0
                
                

    def deleteById(self, id):
        self.c.execute("""DELETE * FROM %s 
                            WHERE id=?""" % self.table_name, (id,))

    def getRowCount(self):
        try: 
            self.c.execute("""SELECT Count(*) FROM %s""" % self.table_name)
            count=self.fetchOne(0)
        except:
            count=0
        return count

    def executeStatement(self, statement, *p):
        self.c.execute(statement, p)
        
    def commit(self):
        self.conn.commit()
        
    def rowCount(self):
        return self.c.rowcount
        
    def fetchOne(self, default=None):
        try: entry=self.c.fetchone()[0]
        except: entry=default
        return entry

    def fetchAll(self, default=None):
        try: entries=self.c.fetchall()
        except: entries=default
        return entries
    
    def fetchOneEx(self, default=None):
        try:
            entry=self.fetchOne()
            data=self.makeDict(entry)
        except:
            data=default
        return data

    def fetchOneEx2(self):
        try:
            entry=self.fetchOne()
            data=self.makeDict(entry)
        except:
            data=self.makeEmptyDict()
        return data
    
    def fetchAllEx(self, default=None):
        result=[]
        try:
            entries=self.fetchAll()
            for entry in entries:
                data=self.makeDict(entry)
                result.append(data)
        except:
            result=default
        return result

    def fetchAllEx2(self):
        result=[]
        try:
            entries=self.fetchAll()
            for entry in entries:
                data=self.makeDict(entry)
                result.append(data)
        except:
            result=[self.makeEmptyDict()]
        return result

    def getPage(self, limit=100):
        statement="""SELECT * FROM %s 
                        ORDER BY updated DESC LIMIT %s""" % (self.table_name, limit)
        self.executeStatement(statement)
        return self.fetchAll()
    
    def getLatestUpdated(self):
        statement="""SELECT * FROM %s 
                        ORDER BY updated DESC LIMIT 1""" % self.table_name
        self.executeStatement(statement)
        return self.fetchOne()
        
        
