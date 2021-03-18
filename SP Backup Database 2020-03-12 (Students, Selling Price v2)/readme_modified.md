# Readme Backup Database Files

This archive contains backup database files and scripts for students working on Structured Programming. These resources are meant to allow them to work on the final individual assignment if the preceding one has not been successful for whatever reason.

Created by Nick Roumimper (nick.roumimper@hu.nl).

## Contents

The following files are included in this package:
- A Python script used to define the schema for the PostgreSQL database (psql_setup_modified.py);
- A Python script that uploads the included .csv files directly to the PostgreSQL database (psql_copyfrom.py);
- Four .csv-files that contain much of the data from the MongoDB, generated with a specialized script (script not included!).

In order to use the included Python scripts, the line at the top setting up the connection needs to be changed to contain appropriate credentials.

## Design (Philosophy)

These .csv files contain a lot more information and relations between tables than the first, rudimentary version. In order to understand the structure of this code, it is helpful to get an idea of why it has been set up this way.

- Little normalization. In order to keep the structure easy to comprehend, the number of tables has been kept to a minimum; from the three base data sets, only four separate tables have been constructed. Records can therefore have plenty of null values (especially the complex product objects). This has the advantage of simplifying most queries.
- Heavy culling. The number of attributes stored in this database has been heavily reduced; any attributes that are sparse or meaningless (or both) have been omitted from the schema. For example, the session objects can maintain an immense history of mostly incomprehensible events. Many types of events have simply been thrown out, where only the ones relating to the customer funnel in some way have been maintained. Although it would technically have been easier to simply copy every single event, a lot of data has simply been parsed out.
- Intensive preprocessing. Aside from the many special cases hiding in the data, I've chosen to combine and reparse a number of fields according to my own standards. For example, in many cases, the products' MSRP (manufacturer's suggested retail price) was stored in a field called mrsp (with the 's' and 'r' switched). I've chosen to map to the correct abbreviation. Similarly, booleans were used to signify the device type in sessions (mobile, pc and tablet). After some research I've ensured that every session is mapped to at most one of these (only 'other' in a few incongruent cases). For more information on the choices made, see the next section.
- Hardly any field optimization. The schema only refers to the most rudimentary datatypes; significant improvements could be made by limiting field lengths, for example. Let's call this one of the disadvantages of using the teachers' version of the data. 

## Schema Explanation

I've here copied over the CREATE statements for the database's schema and annotated them with some additional context where applicable. 

    CREATE TABLE products  // with many non-normalized fields that lead to a sparse table  
        (id VARCHAR PRIMARY KEY,  
         name VARCHAR,  
         brand VARCHAR,  
         type VARCHAR,  
         category VARCHAR,  
         subcategory VARCHAR,  
         subsubcategory VARCHAR,  // subsubsubcategory is always null, so omitted  
         targetaudience VARCHAR,  // combination of properties.doelgroep and gender, in that order  
         msrp INTEGER,  // mapped to the correct spelling, from "mrsp"  
         discount INTEGER,  
         sellingprice INTEGER,  
         deal VARCHAR,  
         description VARCHAR); // the entire description, may be interesting for text mining?    
      
    CREATE TABLE profiles  
        (id VARCHAR PRIMARY KEY,  
         latestactivity TIMESTAMP,  
         segment VARCHAR); 
      
    CREATE TABLE profiles_previously_viewed  
        (profid VARCHAR,  
         prodid VARCHAR,  
         FOREIGN KEY (profid) REFERENCES profiles (id),  
         FOREIGN KEY (prodid) REFERENCES products (id));  
      
    CREATE TYPE d_type AS ENUM ('mobile', 'tablet', 'pc', 'other');  // enumeration used for device types
    CREATE TABLE sessions  
        (id VARCHAR PRIMARY KEY,  
         profid VARCHAR,  
         segment VARCHAR,  
         sale BOOLEAN,  
         starttime TIMESTAMP,  
         endtime TIMESTAMP,  
         duration INTEGER,         // duration in seconds
         os VARCHAR,               // compiled value, based on os.familiy and os.version number
         devicefamily VARCHAR,     // direct copy of device family
         devicetype d_type,        // determined based on the is_mobile/is_pc/is_tablet booleans, translated to max. 1
         FOREIGN KEY (profid) REFERENCES profiles (id));  
