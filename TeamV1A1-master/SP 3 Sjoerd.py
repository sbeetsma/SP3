import PostgresDAO
from datetime import datetime

def query_filter_product(_select, _from, _where):
    query = f"SELECT {_select} FROM {_from} WHERE "

    for attribute in _where:
        query += f"{attribute} = %s and "
    query = query[:-5]
    return query


def create_rec_table_query(table_name, attributes_datatypes):
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

    return table_query

def content_filter_fill(db, attributes, table, attributes_datatypes):

    # connect & cursor
    db.connect_and_cursor('connect')

    # maak een nieuwe tabel aan in de relationele database voor de recommendation rule
    querz = create_rec_table_query(table, attributes_datatypes)
    print(querz)
    db.query(querz, (attributes_datatypes, ), commit_changes=True)

    # query constructen doormiddel van een functie waardoor makkelijk meerdere attributen gekozen kunnen worden
    filter_products_query = query_filter_product('id', 'PRODUCTS', attributes.split(', '))
    filter_products_query += " order by random() limit 4;"

    # query voor het verkrijgen van alle combinaties van de meegegeven attributen (attributen zelf niet hun waardes)
    attribute_combs = atttribute_combinations(db, attributes, 'PRODUCTS')

    data_list = []
    # voor elke attribuut combinatie
    for comb in attribute_combs:

        # select 4 random producten waarbij de attributen overeen komt

        recs = db.query(filter_products_query, comb, expect_return=True)

        # voeg de producten  toe aan een lijst
        upload_list = [recs[i][0]for i in range(len(recs))]
        # eerste elementen in uploadlist zijn de attributen, daarna komen de (product) recommendations
        upload_list = tuple([*list(comb), *upload_list])
        # append naar lijst die alle upload lists bevat
        data_list.append((upload_list,))
    # insert de rows van de recommendation tabel
    db.many_update_queries(
        f"INSERT INTO {table} VALUES %s", data_list)
    # many update queries closed ook de cursor en connectie


def collaborative_filter_fill(db, attributes, table, attributes_datatypes):
    # connect & cursor
    db.connect_and_cursor('connect')

    filter_list = attributes.split(', ')

    # maak een nieuwe tabel aan in de relationele database voor de recommendation rule
    querz = create_rec_table_query(table, attributes_datatypes)
    db.query(querz, (attributes_datatypes, ), commit_changes=True)


    # query voor het verkrijgen van alle combinaties van de meegegeven attributen (attributen zelf niet hun waardes)
    attribute_combs = atttribute_combinations(db, attributes, 'PROFILES')
    filter_profiles_query = query_filter_product('id', 'PROFILES', attributes.split(', '))

    data_list = []
    c = 0
    for comb in attribute_combs:

        # alle profile id's opvragen met gegeven eigenschappen
        profile_ids = db.query(filter_profiles_query, parameters=comb, expect_return=True)

        # de profile id's toevoegen aan een lijst
        upload_list = [profile_ids[i][0] for i in range(len(profile_ids))]

        # select 4 random producten waarbij de attributen overeen komt
        c += 1


        if len(upload_list) == 0:
            continue

        upload_list = tuple(upload_list)

        recs = db.query(f"SELECT prodid FROM profiles_previously_viewed WHERE profid IN (SELECT id FROM profiles WHERE id in %s) order by random() limit 4;", parameters=(upload_list, ), expect_return=True)

        recs = tuple([recs[i][0]for i in range(len(recs))])
        upload_list = tuple([*list(comb), *recs])
        data_list.append([upload_list])


    # insert de rows van de recommendation tabel
    #print(data_list)
    db.many_update_queries(
        f"INSERT INTO {table} VALUES %s", data_list)
    # many update queries closed ook de cursor en connectie


def content_recommendation(db, product_id_list, filter, rec_table, products_or_profiles):
    # connect & cursor
    db.connect_and_cursor('connect')
    # lijst van filter mee geven doormiddel van split
    recommendation_query = query_filter_product('pro1, pro2, pro3, pro4', rec_table, filter.split(', '))
    all_recommendations = []
    for product_id in product_id_list:
        attribute_values = db.query(f"SELECT {filter} FROM {products_or_profiles} where id = %s;", (product_id,), expect_return=True)


        # lijst van de product eigenschappen
        upload_list = [attribute_values[0][i] for i in range(len(attribute_values[0]))]

        # zoek in specifieke recommendation table waar de eigenschappen gelijk zijn als die in upload_list
        recommendations = db.query(recommendation_query, (upload_list), expect_return=True)
        # maak een list van deze recommendations
        print(recommendations)
        recommendations = [recommendations[0][i] for i in range(len(recommendations[0]))]
        # voeg (max 4 per tabel) recommendations te aan all_recommendations.
        all_recommendations.append(recommendations)

    print(all_recommendations)
    return all_recommendations
    db.connect_and_cursor('disconnect')

def atttribute_combinations(db, attributes, location):
    attribute_combs = db.query(f"SELECT DISTINCT {attributes} FROM {location};", expect_return=True)
    return attribute_combs


def start_fill(recommendation_type, db, attributes, table, datatypes):
    if recommendation_type == 'content':
        content_filter_fill(db, attributes, table, datatypes)
    elif recommendation_type == 'collab':
        collaborative_filter_fill(db, attributes, table, datatypes)

def start_recommendation(recommendation_rule, db, id_list):
    # alle bestaande rules moeten hieraan toegevoegd worden
    # recommendation based on content filtering 1
    if recommendation_rule == 'content1':
       return content_recommendation(db, id_list, 'category, targetaudience', recommendation_rule, 'products')
    # recommendation based on content filtering rule 2
    elif recommendation_rule == 'content2':
       return content_recommendation(db, id_list, 'msrp, targetaudience', recommendation_rule, 'products')

    # recommendation based on collaborative filtering 1
    elif recommendation_rule == 'collab1':
       return content_recommendation(db, id_list, 'segment', recommendation_rule, 'profiles')

    else:
        print('wrong input for recommendation rule')



#todo make seperate function for first parts of fill function because its the same code
now = datetime.now()

current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)
### CONTENT FILTER

## maak tabel aan en vul deze gebasseerd op de regel producten die dezelfde category en target audience hebben
#content_filter_fill(PostgresDAO.db, 'category, targetaudience', 'rec_test', 'category VARCHAR, targetaudience VARCHAR,')
## maak tabel aan en vul deze gebasseerd op de regel producten die dezelfde msrp en target audience hebben
#content_filter_fill(PostgresDAO.db, 'category, targetaudience', 'rec_test2', 'category VARCHAR, targetaudience VARCHAR,')
#
## vraag recommendations van product id's ['7225', '9196'] op (max 4 per prod id) voor de eerste en tweede content regels
#content_recommendation(PostgresDAO.db, ['7225', '9196'], 'category, targetaudience', 'rec_test', 'products')
#content_recommendation(PostgresDAO.db, ['7225', '9196'], 'category, targetaudience', 'rec_test2', 'products')

# COLLAB FILTER
#collaborative_filter_fill(PostgresDAO.db, 'segment', 'rec_test2', 'segment VARCHAR,')
#content_recommendation(PostgresDAO.db, ['5c0cfab75e0e02000111edf2', '5c0cfaaf5e0e02000111ede9'], 'segment', 'rec_test2', 'profiles')

#s = att_combinations(PostgresDAO.db, 'category, targetaudience', 'products')


#query_where_construct(['test', 'test2'])
now = datetime.now()

current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)


# ## ### FUNCTION CALLS TO FILL RECOMMENDATION RULE TABLES
# Based on content filter 1
start_fill('content', PostgresDAO.db, 'category, targetaudience', 'content1', 'category VARCHAR, targetaudience VARCHAR,')
# Based on content filter 2
start_fill('content', PostgresDAO.db, 'msrp, targetaudience', 'content2', 'msrp INTEGER, targetaudience VARCHAR,')

# Based on collab filter 1
start_fill('collab', PostgresDAO.db, 'segment', 'collab1', 'segment VARCHAR, ')

# ## ### FUNCTION CALLS TO SHOW RECOMMENDATIONS

# Based on content filter 1
start_recommendation('content1', PostgresDAO.db, ['7225', '9196'])
# Based on content filter 2
start_recommendation('content2', PostgresDAO.db, ['7225', '9196'])

# Based on collab filter 1
start_recommendation('collab1', PostgresDAO.db, ['5c0cfab75e0e02000111edf2', '5c0cfaaf5e0e02000111ede9'])


current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)

