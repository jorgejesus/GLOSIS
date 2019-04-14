# =================================================================
#
# Authors: Jorge Samuel Mendes de Jesus <jorge.dejesus@geocat.net>
#
# Copyright (c) 2018 Jorge Samuel Mendes de Jesus
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import sqlite3
import logging
import os
import json
import io
from pyld import jsonld
from pygeoapi.plugin import InvalidPluginError
from pygeoapi.provider.base import BaseProvider, ProviderConnectionError

LOGGER = logging.getLogger(__name__)


class GLOSISProvider(BaseProvider):
    """
    
    Generic provider for SQLITE using sqlite3 module. For GLOSIS data
    This module requires install of libsqlite3-mod-spatialite
    
    TODO: DELETE, UPDATE, CREATE
    """

    def __init__(self, provider_def):
        """
        SQLiteProvider Class constructor

        :param provider_def: provider definitions from yml pygeoapi-config.
                             data,id_field, name set in parent class

        :returns: pygeoapi.providers.base.GLOSISProvider
        """
        BaseProvider.__init__(self, provider_def)

        self.table = provider_def['table']

        self.dataDB = None

        LOGGER.debug('Setting Sqlite-GLOSIS propreties:')
        LOGGER.debug('Data source:{}'.format(self.data))
        LOGGER.debug('Name:{}'.format(self.name))
        LOGGER.debug('ID_field:{}'.format(self.id_field))
        LOGGER.debug('Table:{}'.format(self.table))

    def __response_jsonld(self):
        """Assembles a JSONLD
        
        :returns: JSONLD FeaturesCollection
        
        
        """

#        feature_list = list()
#        for row_data in self.dataDB:
#            row_data = dict(row_data)  # sqlite3.Row is doesnt support pop
#            feature_list.append(row_data)
        

#        return feature_list
        
        
    
    def __response_feature_collection(self):
        """Assembles GeoJSON output from DB query

        :returns: GeoJSON FeaturesCollection
        """

        feature_list = list()
        for row_data in self.dataDB:
            row_data = dict(row_data)  # sqlite3.Row is doesnt support pop
            
            feature = {
                'type': 'Feature'
            }
            feature["geometry"] = json.loads(
                row_data.pop('AsGeoJSON(geom)')
                )
            #feature['properties'] = row_data
            #feature['id'] = feature['properties'].pop(self.id_field)
            feature['id']=row_data[self.id_field]
            feature_list.append(feature)

        feature_collection = {
            'type': 'FeatureCollection',
            'features': feature_list
        }

        return feature_collection

    def __response_feature_hits(self, hits):
        """Assembles GeoJSON/Feature number

        :returns: GeoJSON FeaturesCollection
        """

        feature_collection = {"features": [],
                              "type": "FeatureCollection"}
        feature_collection['numberMatched'] = hits

        return feature_collection

    def __load(self):
        """
        Private method for loading spatiallite,
        get the table structure and dump geometry

        :returns: sqlite3.Cursor
        """

        if (os.path.exists(self.data)):
            conn = sqlite3.connect(self.data)
        else:
            raise InvalidPluginError

        try:
            conn.enable_load_extension(True)
        except AttributeError as err:
            LOGGER.error('Extension loading not enabled: {}'.format(err))
            raise ProviderConnectionError()

        conn.row_factory = sqlite3.Row
        conn.enable_load_extension(True)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT load_extension('mod_spatialite.so')")
            cursor.execute("PRAGMA table_info({})".format(self.table))
        except sqlite3.OperationalError as err:
            LOGGER.error('Extension loading error: {}'.format(err))
            raise ProviderConnectionError()
        result = cursor.fetchall()
        try:
            # TODO: Better exceptions declaring
            # InvalidPluginError as Parent class
            assert len(result), "Table not found"
            assert len([item for item in result
                        if item['pk'] == 1]), "Primary key not found"
            assert len([item for item in result
                        if self.id_field in item]), "id_field not present"
            assert len([item for item in result
                        if 'geom' in item]), "geom column not found"

        except InvalidPluginError:
            raise

        self.columns = [item[1] for item in result if item[1] != 'geom']
        self.columns = ",".join(self.columns)+",AsGeoJSON(geom)"

        return cursor

    def query(self, startindex=0, limit=10, resulttype='results',
              bbox=[], time=None, properties=[], sortby=[]):
        """
        Query Sqlite for all the content.
        e,g: http://localhost:5000/collections/countries/items?
        limit=1&resulttype=results

        :param startindex: starting record to return (default 0)
        :param limit: number of records to return (default 10)
        :param resulttype: return results or hit limit (default results)
        :param bbox: bounding box [minx,miny,maxx,maxy]
        :param time: temporal (datestamp or extent)
        :param properties: list of tuples (name, value)
        :param sortby: list of dicts (property, order)

        :returns: GeoJSON FeaturesCollection
        """
        LOGGER.debug('Querying Sqlite')

        cursor = self.__load()

        LOGGER.debug('Got cursor from DB')

        if resulttype == 'hits':
            res = cursor.execute("select count(*) as hits from {};".format(
                self.table))

            hits = res.fetchone()["hits"]
            return self.__response_feature_hits(hits)

        end_index = startindex + limit
        # Not working
        # http://localhost:5000/collections/countries/items/?startindex=10
        sql_query = "select {} from {} where rowid >= ? \
        and rowid <= ?;".format(self.columns, self.table)

        LOGGER.debug('SQL Query:{}'.format(sql_query))
        LOGGER.debug('Start Index:{}'.format(startindex))
        LOGGER.debug('End Index'.format(end_index))

        self.dataDB = cursor.execute(sql_query, (startindex, end_index, ))

        #jsonld_payload = self.__response_jsonld()
        return self.__response_feature_collection()

    def get(self, identifier):
        """
        Query the provider for a specific
        feature id e.g: /collections/countries/items/1

        :param identifier: feature id

        :returns: GeoJSON FeaturesCollection
        """

        LOGGER.debug('Get item from Sqlite')

        cursor = self.__load()

        LOGGER.debug('Got cursor from DB')

        
        #identifier -->88208607-b776-4580-93a9-731805185578
        LOGGER.debug('Identifier:{}'.format(identifier))
        
        sql_query_profile = "select {} from profile where id==?;".format(self.columns)
        profile_res = cursor.execute(sql_query_profile, (identifier,)).fetchall()
        id_survey = profile_res[0]["id_survey"]
        year = profile_res[0]["year"]
        coord = json.load(io.StringIO(profile_res[0]["AsGeoJSON(geom)"]))["coordinates"]

        

        sql_query_survey = "select * from survey where id==?;"
        survey_res = cursor.execute(sql_query_survey, (id_survey,)).fetchall()

        survey_id_institution=survey_res[0]["id_institution"]
        survey_id_name=survey_res[0]["name"]
        date_start = survey_res[0]["date_start"]
        date_end = survey_res[0]["date_end"] 

        #print(dict(survey_res[0])) #{'id': 'c191af9b-1e00-4819-bc33-c56bb4616690', 'id_institution': '58888d7a-49c1-4e11-b9fb-aa4020adde52', 'name': 'Margaritifer Terra I', 'date_start': '21-03-2039', 'date_end': '21-09-2039'}

        sql_query_profile_obs_cat = "select * from profile_observation_cat where id_profile==?;"
        survey_res = cursor.execute(sql_query_profile_obs_cat, (identifier,)).fetchall()
        for row in survey_res:
            property_cat_id = row['id_property_profile_cat']
            property_value_id = row['id_property_profile_cat_value']
            sql_cat_name = "select name from property_profile_cat where id==?"
            sql_cat_name_value = cursor.execute(sql_cat_name, (property_cat_id,)).fetchall()
            sql_cat_name_value = dict(sql_cat_name_value[0])["name"]
        
            sql_cat_name_value= sql_cat_name_value.lower().replace(" ","_")
            
            sql_query_cat_value ="select name from property_profile_cat_value where id==?"
            sql_cat_value = cursor.execute(sql_query_cat_value, (property_value_id,)).fetchall()
            
            sql_cat_value=dict(sql_cat_value[0])["name"]
            
            #'id_property_profile_cat': '29985106-c6cb-44b5-a408-fc25be8a2867', 'id_property_profile_cat_value': 'f63fd4a7-a3ba-4f1e-80a5-187a2a27d10d'
            #print(dict(survey_res[0]))
        
            doc = {
            "@id":"https://glosis.isric.org/profile/{}".format(identifier),
            "@type": "profile",
            "https://glosis.isric.org/def/survey":{
                "@id":"https://glosis.isric.org/survey/{}".format(id_survey),
                "@type": "https://glosis.isric.org/def/survey",
                "https://glosis.isric.org/def/id_institution": "https://glosis.isric.org/id_institution/{}".format(survey_id_institution),
                "https://glosis.isric.org/def/name_institution":"{}".format(survey_id_name),
                 "https://schema.org/startDate":"{}".format(date_start),
                 "https://schema.org/endDate": "{}".format(date_end),
              },
            "https://glosis.isric.org/def/{}".format(sql_cat_name_value): sql_cat_value,
            "https://schema.org/Date": year, 
            "https://schema.org/GeoCoordinates":{
               "@type": "GeoCoordinates",
               "https://schema.org/latitude": coord[1],
               "https://schema.org/longitude": coord[0],
               }
            }
            
            context = {
                "profile": "https://glosis.isric.org/def/profile",
                "{}".format(sql_cat_name_value): "https://glosis.isric.org/def/{}".format(sql_cat_name_value),
                "year": "https://schema.org/Date",
                "geo": "https://schema.org/GeoCoordinates",
                "latitude": "https://schema.org/latitude",
                "longitude": "https://schema.org/longitude",
                "survey": "https://glosis.isric.org/def/survey",
                "name": "https://glosis.isric.org/def/name_institution",
                "id_institution": "https://glosis.isric.org/def/id_institution",
                "date_start":"https://schema.org/startDate",
                "date_end": "https://schema.org/endDate"
            }
    
            compacted = jsonld.compact(doc, context,context)
        return compacted


    def __repr__(self):
        return '<SQLiteProvider> {},{}'.format(self.data, self.table)
