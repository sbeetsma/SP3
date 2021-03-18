import psycopg2

#Vul hier je eigen PostgreSQL credentials in:
host = "localhost"
database = "SP3"
user = "postgres"
password = "password"
port = "5432"
#try not to push them to github



class PostgreSQLdb:
    """A PostgreSQL (relational) database.

    Attributes:
        host: the hostname the database is hosted at (presumably localhost in this usecase).
        database: the name of the database (rcmd for all the group members).
        user: the user the database belongs to according to pgadmin (presumably postgres).
        password: the database password.
        port: the port the database is hosted at (presumably 5432 if DB is hosted on windows machine).
        connection: a psycopg2.extensions.cursor object that represents a connection to the database.
        cursor: a psycopg2.extensions.connection that represents a cursor in the database."""
    def __init__(self, host: str, database: str, user: str, password: str, port: str):
        """Initialize class instance.

        Args:
            host: the hostname the database is hosted at (presumably localhost in this usecase).
            database: the name of the database (rcmd for all the group members).
            user: the user the database belongs to according to pgadmin (presumably postgres).
            password: the database password.
            port: the port the database is hosted at.
            """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection = None
        self.cursor = None

    def connect(self):
        """Connects to the database.
        Assings a connection object to self.connection."""
        self.connection = psycopg2.connect(
            host = self.host,
            database = self.database,
            user = self.user,
            password = self.password,
            port = self.port
        )

    def summon_cursor(self):
        """Creates a cursor within the database.
        Assigns a cursor object to self.cursor."""
        self.cursor = self.connection.cursor()

    def close_connection(self):
        """Closes the connection with the database.
        Sets self.connection to none."""
        self.connection.close()
        self.connection = None

    def close_cursor(self):
        """Closes the cursor within the database.
        Sets self.cursor to none."""
        self.cursor.close()
        self.cursor = None

    def connect_and_cursor(self, connect_disconnect):
        """Connects to the database and summons cursor, or closes cursor and closes database connection
        by using the existing functions for (dis)connecting and closing/summoning a cursor"""
        if connect_disconnect == 'connect':
            self.connect()
            self.summon_cursor()
        elif connect_disconnect == 'disconnect':
            self.close_cursor()
            self.close_connection()

    def bare_query(self, query: str, parameters: tuple = None):
        """Executes an SQL query in the database.
        Able to sanatize inputs with the parameters parameter.

        Args:
            query:
                The SQL query to execute.
                May contain '%s' in place of parameters to let psycopg2 automatically format them.
                The values to replace the %s's with can be passed with the parameters parameter.
            parameters: tuple containing parameters to replace the %s's in the query with."""
        if parameters == None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, parameters)

    def fetch_query_result(self) -> list[tuple]:
        """Get the results from the most recent query.

        Returns:
            list containing a tuple for every row in the query result."""
        return self.cursor.fetchall()

    def commit_changes(self):
        """Commits any changes made in queries."""
        self.connection.commit()

    def query(self, query: str, parameters: tuple = None, expect_return: bool = False, commit_changes: bool = False) -> list[tuple] or None:
        """Opens a connection to the DB, opens a cursor, executes a query, and closes everything again.
        Also retrieves query result or commits changes if relevant.

        Args:
            query:
                The SQL query to execute.
                May contain '%s' in place of parameters to let psycopg2 automatically format them.
                The values to replace the %s's with can be passed with the parameters parameter.
            parameters: tuple containing parameters to replace the %s's in the query with.
            expect_return: bool for wether the query should expect a return.
            commit_changes: bool for wether changes were made to the DB that need to be committed.

        Returns:
            if expect_return:
                list containing a tuple for every row in the query result.
            else:
                None"""
        self.bare_query(query, parameters)
        output = None
        if expect_return:
            output = self.fetch_query_result()
        if commit_changes:
            self.commit_changes()
        return output

    def many_update_queries(self, query: str, data_list: list[tuple]):
        """Execute a single query that updates the DB with many different values without constantly opening/closing cursors/connections.

        Args:
            query:
                The SQL query to execute with every dataset in data_list.
                Must contain '%s' in place of parameters to let psycopg2 automatically format them.
                The values to replace the %s's with must be passed with the parameters parameter.
            data_list:
                list containing a tuple for every query that has to be excecuted."""
        self.connect()
        self.summon_cursor()
        self.cursor.executemany(query, data_list)
        self.commit_changes()
        self.close_cursor()
        self.close_connection()


    def regenerate_db(self, ddl_source: str):
        """Empties all knows tables in the DB, and reconstructs everything according to the DDL(SQL) file provided.

        Args:
            ddl_source: the file path/name of the ddl script."""
        with open(ddl_source, "r") as file:
            file_object = file.read().replace('\n', '')
        query_list = file_object.split(";")
        for query in query_list:
            if query != "":
                self.query(query + ";", commit_changes=True)


# connect met database
db = PostgreSQLdb(host, database, user, password, port)

def construct_query_where_and(_select, _from, _where):
    """"Function to construct a select X from Y where att1 = %s or att2 = %s etc...  works with only 1 attribute with no maximum limit for amount of attributes
    args:
        _select: select what_ ex: id
        _from: from where ex: products
        _where: list of attributes(names not values).
    returns:
        query: ex multiple attributes: SELECT id FROM products WHERE category = %s and targetaudience = %s"""

    query = f"SELECT {_select} FROM {_from} WHERE "
    # for each attribute add to the query "attribute = %s or "
    for attribute in _where:
        query += f"{attribute} = %s or "
    # remove the "or " at the end of the query
    query = query[:-4]
    return query


def create_rec_table_query(db, table_name, attributes_datatypes):
    """Function to construct and execute a query for table creation where the product recommendations will be stored
    args:
        db: database object where to create the table. db is a object from PostgresDAO
        table_name: the name of the table that will be created. the table name will be the name of the recommendation rule
        attributes_datatypes:   the attributes which the recommendation engine will use to fill the tables and their data type ex: 'category VARCHAR, targetaudience VARCHAR,'
                                all attributes and datatypes must be stored in a single string"""
    table_query = f"""
    DROP TABLE IF EXISTS {table_name};
    CREATE TABLE {table_name}
    (
    {attributes_datatypes}
    pro1 VARCHAR,
    pro2 VARCHAR,
    pro3 VARCHAR,
    pro4 VARCHAR,
    FOREIGN KEY (pro1)
    REFERENCES
    products(id),
    FOREIGN
    KEY(pro2)
    REFERENCES
    products(id),
    FOREIGN
    KEY(pro3)
    REFERENCES
    products(id),
    FOREIGN
    KEY(pro4)
    REFERENCES
    products(id)
    );"""
    db.query(table_query, (attributes_datatypes,), commit_changes=True)
