import PostgresDAO
import random
from datetime import datetime


print(PostgresDAO.db)

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
    db.connect()
    db.summon_cursor()

    # maak een nieuwe tabel aan in de relationele database voor de recommendation rule
    querz = create_rec_table_query(table, attributes_datatypes)
    print(querz)
    db.query(querz, (attributes_datatypes, ), commit_changes=True)

    # filter als string is nodig voor de eerste query, voor de tweede zijn de elementen van filter
    filter_list = attributes.split(', ')
    # query constructen doormiddel van een functie waardoor makkelijk meerdere attributen gekozen kunnen worden
    filter_products_query = query_filter_product('id', 'PRODUCTS', filter_list)
    filter_products_query += " order by random() limit 4;"
    #filter_products_query += " order by random() limit 4;"
    # query voor het verkrijgen van alle combinaties van de meegegeven attributen (attributen zelf niet hun waardes)
    attribute_combinations = db.query(f"SELECT DISTINCT {attributes} FROM {'PRODUCTS'};", expect_return=True)
    data_list = []
    # voor elke attribuut combinatie
    for comb in attribute_combinations:

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

def content_recommendation(db, product_id_list, filter, rec_table, products_or_profiles):
    # connect & cursor
    db.connect()
    db.summon_cursor()
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
        recommendations = [recommendations[0][i] for i in range(len(recommendations[0]))]
        # voeg (max 4 per tabel) recommendations te aan all_recommendations.
        all_recommendations.append(recommendations)

    print(all_recommendations)

    db.close_cursor()
    db.close_connection()

def collabrative_filter_fill(db, attributes, table, attributes_datatypes):
    # connect & cursor
    db.connect()
    db.summon_cursor()

    filter_list = attributes.split(', ')

    # maak een nieuwe tabel aan in de relationele database voor de recommendation rule
    querz = create_rec_table_query(table, attributes_datatypes)

    db.query(querz, (attributes_datatypes, ), commit_changes=True)


    # query voor het verkrijgen van alle combinaties van de meegegeven attributen (attributen zelf niet hun waardes)
    attribute_combinations = db.query(f"SELECT DISTINCT {attributes} FROM {'PROFILES'};", expect_return=True)
    filter_products_query = query_filter_product('id', 'PROFILES', attributes.split(', '))
    data_list = []
    c = 0
    for comb in attribute_combinations:
        profile_ids = db.query(f"SELECT id FROM {'PROFILES'} where segment = %s;", parameters=comb, expect_return=True)
        upload_list = [profile_ids[i][0] for i in range(len(profile_ids))]

        # select 4 random producten waarbij de attributen overeen komt
        c += 1


        try:
            upload_list[0]
        except:
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









now = datetime.now()

current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)
### CONTENT FILTER

## maak tabel aan en vul deze gebasseerd op de regel producten die dezelfde category en target audience hebben
#content_filter_fill(PostgresDAO.db, 'category, targetaudience', 'rec_test', 'category VARCHAR, targetaudience VARCHAR,')
## maak tabel aan en vul deze gebasseerd op de regel producten die dezelfde msrp en target audience hebben
#content_filter_fill(PostgresDAO.db, 'msrp, targetaudience', 'rec_test2', 'msrp INTEGER, targetaudience VARCHAR,')
#
## vraag recommendations van product id's ['7225', '9196'] op (max 4 per prod id) voor de eerste en tweede content regels
content_recommendation(PostgresDAO.db, ['7225', '9196'], 'category, targetaudience', 'rec_test', 'products')
#content_recommendation(PostgresDAO.db, ['7225', '9196'], 'msrp, targetaudience', 'rec_test2')

# COLLAB FILTER
#collabrative_filter_fill(PostgresDAO.db, 'segment', 'rec_test2', 'segment VARCHAR,')
content_recommendation(PostgresDAO.db, ['5c0cfab75e0e02000111edf2', '5c0cfaaf5e0e02000111ede9'], 'segment', 'rec_test2', 'profiles')




#query_where_construct(['test', 'test2'])
now = datetime.now()

current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)



