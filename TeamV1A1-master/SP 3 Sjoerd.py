import PostgresDAO
from PostgresDAO import construct_query_where_and, create_rec_table_query
# 2 functies specifiek gemaakt voor opdracht 3 staan in PostgresDAO om de functies die queries constructen gescheiden te houden.

### Fill functions
def attribute_combinations(db, attributes, location):
    """Function that returns all existing attribute combinations
        args:
            db: database which to search the combinations. db is a object from PostgresDAO
            attributes: list of attributes which existing combinations must be found
            location: from where?: string 'products' or 'profiles'
        returns:
            attribute_combs: query result, all existing attribute combinations"""
    return db.query(f"SELECT DISTINCT {attributes} FROM {location};", expect_return=True)

def content_filter_fill(db, attributes, table, attributes_datatypes):
    """Function to fill a table in a database based on a content filter rule
    the rule will choose recommendations based on if given product attribute(s) are equal
    for example the attribute category and targetaudience
    args:
        db: database object to fill the recommendation rule table. db is a object from PostgresDAO
        attributes: list of attributes to base the recommendations on
        table: string of the name of the recommendation rule, this will be the name for the table
        attribute_datatypes: string of the attributes and datatypes required to create the table"""

    # connect & cursor
    db.connect_and_cursor('connect')

    # maak een nieuwe tabel aan in de relationele database voor de recommendation rule
    create_rec_table_query(db, table, attributes_datatypes)

    # query constructen welke eigenschappen/attributes gefilterd moet worden.
    filter_products_query = construct_query_where_and('id', 'PRODUCTS', attributes.split(', '))
    # aan query adden zodat alleen 4 random producten terug wordt gegeven
    filter_products_query += " order by random() limit 4;"

    # elke mogelijke combinatie attributen van gegeven attributen (mogelijk mits de combinatie ook voorkomt in de db)
    attribute_combs = attribute_combinations(db, attributes, 'PRODUCTS')

    # uiteindelijke lijst van data die wordt geupload in de tabel van de recommendation rule zodat dit in 1 executemany statement kan worden ingevuld
    data_list = []

    # voor combinatie in bestaande attribute combinaties
    for comb in attribute_combs:

        # recs (productids) zijn (max) 4 recommendations doormiddel van een query met filter_products_query
        recs = db.query(filter_products_query, comb, expect_return=True)

        # voeg de ids toe aan een lijst
        upload_list = [recs[i][0]for i in range(len(recs))]

        # eerste elementen in uploadlist zijn de attributen/eigenschappen, daarna komen de (product) recommendations
        upload_list = tuple([*list(comb), *upload_list])
        # append naar de data_list
        data_list.append((upload_list,))

    # data_list bevat nu alle combinaties van eigenschappen met de bijbehorende recommendations voor die eigenschappen
    # insert de rows van de recommendation tabel
    db.many_update_queries(
        f"INSERT INTO {table} VALUES %s", data_list)
    # many update queries closed de cursor en connectie

def collaborative_filter_fill(db, attributes, table, attributes_datatypes):
    """Function to fill a table in a database based on a collaborative filter rule
    the rule will choose recommendations based on if given profile attribute(s) are equal
    for example the attribute segment. multiple attributes are possible
    args:
        db: database object where to fill the recommendation rule table. db is a object from PostgresDAO
        attributes: list of attributes to base the recommendations on
        table: string of the name of the recommendation rule, this will be the name for the table
        attribute_datatypes: string of the attributes and datatypes required to create the table"""
    # connect & cursor
    db.connect_and_cursor('connect')

    # maak een nieuwe tabel aan in de relationele database voor de recommendation rule
    create_rec_table_query(db, table, attributes_datatypes)

    # elke mogelijke combinatie van gegeven attributen (mogelijk mits ze ook voorkomen in de db)
    attribute_combs = attribute_combinations(db, attributes, 'PROFILES')
    # query constructen welke eigenschappen/attributes gefilterd moet worden.
    filter_profiles_query = construct_query_where_and('id', 'PROFILES', attributes.split(', '))

    # uiteindelijke lijst van data die wordt geupload in de tabel van de recommendation rule zodat dit in 1 executemany statement kan worden ingevuld
    data_list = []

    # voor combinatie in bestaande attribute combinaties
    for comb in attribute_combs:
        # alle profile id's opvragen met gegeven eigenschappen
        # profile id's die comb als attributen waardes bevat doormiddel van een query met filter_profiles_query
        profile_ids = db.query(filter_profiles_query, parameters=comb, expect_return=True)

        # de profile id's toevoegen aan een lijst
        upload_list = [profile_ids[i][0] for i in range(len(profile_ids))]

        # hard coded omdat de volgende query niet werkt met de eigenschap none die 0 profiles terug geeft daarom skip naar de volgende combinatie
        if len(upload_list) == 0:
            continue

        upload_list = tuple(upload_list)
        # execute query om product ids op te vragen die in previously viewed staan met een profielid waarvan het profiel id voorkomt in de upload_list met profiel ids
        recs = db.query(f"SELECT prodid FROM profiles_previously_viewed WHERE profid IN (SELECT id FROM profiles WHERE id in %s) order by random() limit 4;", parameters=(upload_list, ), expect_return=True)
        # alle product ids voor de recommendation
        recs = tuple([recs[i][0]for i in range(len(recs))])
        # eerste elementen in uploadlist zijn de attributen/eigenschappen, daarna komen de (product) recommendations
        upload_list = tuple([*list(comb), *recs])
        # append naar de data_list
        data_list.append([upload_list])

    # data_list bevat nu alle combinaties van eigenschappen met de bijbehorende recommendations voor die eigenschappen
    # insert de rows van de recommendation tabel
    db.many_update_queries(
        f"INSERT INTO {table} VALUES %s", data_list)
    # many update queries closed ook de cursor en connectie

# Pull functions
def pull_recommendation(db, id_list, attributes, rec_rule, products_or_profiles):
    """Function to pull recommendations from database
        args:
            db: database object where to find the recommendation. db is a object from PostgresDAO
            id_list: list of ids where the recommendations will be based on. has to be either a list of profile ids or product ids not mixed
            attributes: list of attributes which the recommendation rule uses
            rec_rule: string of recommendation rule name which is also the table name for that rule
            products_or_profiles: string 'products' or 'profiles' based on what type of id will the recommendation be?
        returns:
        all_recommendations: a list of lists which includes a maximum of 4 product id's per id in id_list"""
    # connect & cursor
    db.connect_and_cursor('connect')
    # lijst van attributes mee geven doormiddel van split
    recommendation_query = construct_query_where_and('pro1, pro2, pro3, pro4', rec_rule, attributes.split(', '))
    # wordt een lijst van lijsten die de product recommendations bevat. (max) 4 producten per product/profile id
    all_recommendations = []
    # voor elk product uit de lijst meegegeven product ids
    for ID in id_list:
        # de eigenschappen van het product
        attribute_values = db.query(f"SELECT {attributes} FROM {products_or_profiles} where id = %s;", (ID,), expect_return=True)

        # lijst van de product eigenschappen
        upload_list = [attribute_values[0][i] for i in range(len(attribute_values[0]))]

        # haal de recommendation op waar de eigenschappen gelijk zijn als die in upload_list
        recommendations = db.query(recommendation_query, (upload_list), expect_return=True)
        # maak een list van deze recommendations
        recommendations = [recommendations[0][i] for i in range(len(recommendations[0]))]
        # recommendations te aan all_recommendations.
        all_recommendations.append(recommendations)
    # close cursor and disconnect from db
    db.connect_and_cursor('disconnect')
    return all_recommendations

# start fill
def start_fill(recommendation_type, db, attributes, table, datatypes):
    """function to start filling functions, with this function new rules are made and can easily be created based on what type of rule (content/collab) and which attributes that rule will filter.
        args:
            recommendation_type: string 'content' or 'collab' to specify which filling function has to be started.
            rest of the args are described in the fill functions"""

    if recommendation_type == 'content':
        content_filter_fill(db, attributes, table, datatypes)
    elif recommendation_type == 'collab':
        collaborative_filter_fill(db, attributes, table, datatypes)
# start pull / recommendation
def start_recommendation(recommendation_rule, db, id_list):
    """function to start pull_recommendations function with certain parameters based on which recommendation rule is given
        args:
            recommendation_rule: string of the name of the recommendation rule to use
            rest of the args are described in the fill functions"""

    # alle bestaande rules moeten hieraan toegevoegd worden

    # recommendation based on content filtering 1
    if recommendation_rule == 'content_1':
       return pull_recommendation(db, id_list, 'category, targetaudience', recommendation_rule, 'products')
    
    # recommendation based on content filtering rule 2
    elif recommendation_rule == 'content_2':
       return pull_recommendation(db, id_list, 'msrp, targetaudience', recommendation_rule, 'products')

    # recommendation based on collaborative filtering 1
    elif recommendation_rule == 'collab_1':
       return pull_recommendation(db, id_list, 'segment', recommendation_rule, 'profiles')

    else:
        print('wrong parameter for recommendation rule this rule does not exist!')

# FUNCTION CALLS TO FILL RECOMMENDATION RULE TABLES once the fill functions are called they can be removed to check recommendations without filling again

# CONTENT
# Based on content filter_1
start_fill('content', PostgresDAO.db, 'category, targetaudience', 'content_1', 'category VARCHAR, targetaudience VARCHAR,')
# Based on content filter_2
start_fill('content', PostgresDAO.db, 'msrp, targetaudience', 'content_2', 'msrp INTEGER, targetaudience VARCHAR,')
# COLLAB
# Based on collab filter_1
start_fill('collab', PostgresDAO.db, 'segment', 'collab_1', 'segment VARCHAR, ')

# FUNCTION CALLS TO SHOW RECOMMENDATIONS

# CONTENT
# Based on content_1 rule
start_recommendation('content_1', PostgresDAO.db, ['7225', '9196'])
#Based on content_2 rule
start_recommendation('content_2', PostgresDAO.db, ['7225', '9196'])

# COLLAB
# Based on collab_1 rule
start_recommendation('collab_1', PostgresDAO.db, ['5c0cfab75e0e02000111edf2', '5c0cfaaf5e0e02000111ede9'])
