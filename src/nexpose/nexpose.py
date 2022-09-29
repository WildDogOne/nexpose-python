import json
from pprint import pprint
import logging
import requests

"""
Configure Logging
"""
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class nexpose():
    def __init__(self, config):
        """
        :param config: Configuration dict, needs URL, Authentication and Certificate
        {
        "url":"https://ivm.host",
        "auth":"base64 encoded username:password",
        "cert":"Path to certificate or False",
        }
        """
        self.apiurl = config["url"]
        self.auth = config["auth"]
        self.cert = config["cert"]
        self.header = {'Content-Type': "application/json",
                       'Authorization': "Basic " + self.auth,
                       'Accept': "*/*",
                       'cache-control': "no-cache"}

    def getPagination(self, url):
        """
        :param url: URL To paginate through
        :return: Response of pagination
        """
        go = 1
        page = 0
        output = []
        while go == 1:
            params = {"size": 500, "page": page}
            response = requests.request("GET",
                                        url,
                                        headers=self.header,
                                        verify=self.cert,
                                        params=params).json()
            totalPages = response["page"]["totalPages"]
            if totalPages > page:
                if "output" in locals():
                    output = output + response["resources"]
                else:
                    output = response["resources"]
                page += 1
                logger.debug(f"Page Number {page} Total Pages: {totalPages}")
            else:
                go = 0
        return output

    def _get(self, url, size=500):
        """
        :param url: API URL to get
        :return: Returns response of URL
        """
        params = {"size": size}
        response = requests.get(url,
                                headers=self.header,
                                verify=self.cert,
                                params=params)
        if response.status_code != 200:
            logger.error("Unable to process GET")
            logger.error(f"Status code {response.status_code}")
            return response.json()
        return response.json()

    def _delete(self, url):
        """
        :param url: API URL to get
        :return: Returns response of URL
        """
        response = requests.delete(url,
                                headers=self.header,
                                verify=self.cert)
        if response.status_code != 200:
            logger.error("Unable to process DELETE")
            logger.error(f"Status code {response.status_code}")
            return response.json()
        return response.json()

    def post(self, url, data):
        """
        :param url: URL to POST Data to
        :param data: Data to POST
        :return: Returns response of API
        """
        response = requests.request("POST",
                                    url,
                                    headers=self.header,
                                    verify=self.cert,
                                    json=data).json()
        return response

    def get_sites(self, size=500):
        """
        :param size: INT of page size (0 = unlimited)
        :return: Returns all Sites
        """
        url = self.apiurl + "/api/3/sites"
        if size == 0 or size > 500:
            return self.getPagination(url)
        else:
            return self._get(url, size)["resources"]

    def get_site_assets(self, site_id=None, size=0):
        """
        :param site_id:
        :param size:
        :return: Returns all Assets from a site
        """
        if site_id:
            url = self.apiurl + "/api/3/sites/" + str(site_id) + "/assets"
            if size == 0 or size > 500:
                return self.getPagination(url)
            else:
                return self._get(url, size)["resources"]
        else:
            logger.error("Missing Site ID Parameter")

    def get_assets(self, size=0):
        """
        :param size: INT of page size (0 = unlimited)
        :return: Returns all assets
        """
        url = self.apiurl + "/api/3/assets"
        if size == 0 or size > 500:
            return self.getPagination(url)
        else:
            return self._get(url, size)["resources"]

    def _put(self, url, payload):
        response = requests.request("PUT",
                                    url,
                                    headers=self.header,
                                    verify=self.cert,
                                    data=payload)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 500:
            logger.warning("PUT Failed")
            return response.json()
        else:
            logger.error("unable to put")
            logger.error(f"{response.text}")
            logger.error(f"Status Code: {response.status_code}")

    def get_scans(self):
        """
        :return: Returns all Scans
        """
        url = self.apiurl + "/api/3/scans"
        return self.getPagination(url)

    def stop_scan(self, scan_id):
        """
        :param scan_id: INT: ID if Scan to stpo
        :return:
        """
        url = self.apiurl + "/api/3/scans/" + str(scan_id) + "/stop"
        return self._post(url)

    def start_scan(self, site_id, template_id):
        url = self.apiurl + "/api/3/sites/" + str(site_id) + "/scans"
        payload = {
            "templateId": template_id
        }
        self._post(url, payload)

    def _post(self, url, payload={}):
        response = requests.request("POST",
                                    url,
                                    headers=self.header,
                                    verify=self.cert,
                                    json=payload)
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        if response.status_code == 500:
            logger.warning("POST Failed")
            return response.json()
        else:
            logger.error("unable to post")
            logger.error(f"{response.text}")
            logger.error(f"Status Code: {response.status_code}")

    def _post_paginated(self, url, payload={}):
        go = 1
        page = 0
        output = []
        while go == 1:
            params = {"size": 500, "page": page}
            response = requests.request("POST",
                                        url,
                                        headers=self.header,
                                        verify=self.cert,
                                        params=params,
                                        json=payload).json()
            totalPages = response["page"]["totalPages"]
            if totalPages > page:
                if "output" in locals():
                    output = output + response["resources"]
                else:
                    output = response["resources"]
                page += 1
                logger.debug(f"Page Number {page} Total Pages: {totalPages}")
            else:
                go = 0
        return output

    def set_site_scan_template(self, site_id, scan_template):
        """
        :param site_id: INT: Site ID
        :param scan_template: STR: ID of the Scanning Template
        :return: Result Code
        """
        url = self.apiurl + "/api/3/sites/" + str(site_id) + "/scan_template"
        payload = scan_template
        response = self._put(url, payload)
        return response

    def get_scan(self, id):
        """
        :return: Returns Scan by ID
        """
        url = self.apiurl + "/api/3/scans/" + str(id)
        return self._get(url)

    def get_asset(self, id):
        """
        :return: Returns Asset by ID
        """
        url = self.apiurl + "/api/3/assets/" + str(id)
        return self._get(url)

    def find_assets(self, filters, match):
        url = self.apiurl + "/api/3/assets/search"
        payload = {
            "filters": filters,
            "match": match
        }
        return self._post_paginated(url, payload)

    def getTags(self):
        """
        :return: Returns all Tags
        """
        url = self.apiurl + "/api/3/tags"
        return self.getPagination(url)

    def get_asset_vulnerabilities(self, asset_id):
        """
        :param asset_id: Asset ID to query
        :return: Returns all Vulnerabilities of an asset
        """
        url = self.apiurl + "/api/3/assets/" + str(asset_id) + "/vulnerabilities"
        return self.getPagination(url)

    def get_vulnerability(self, vuln_id):
        """
        :param vuln_id: Vulnerablity ID to query
        :return: Returns all Vulnerabilities of an asset
        """
        url = self.apiurl + "/api/3/vulnerabilities/" + str(vuln_id)
        return self._get(url)

    def postTag(self, name):
        """

        :return: Returns Status
        This function is used to add new Owner Tags to DB
        """
        url = self.apiurl + "/api/3/tags"

        data = {
            "name": name,
            "type": "owner",
            "color": "default"}
        self.post(url, data)

    def getOwnerTags(self):
        """
        :return: Returns all Owner Tags
        """
        tags = self.getTags()
        output = {}
        for tag in tags:
            if tag["type"] == "owner":
                output[tag["name"]] = tag["id"]
        return output

    def putTagtoAsset(self, tagID, assetID):
        """
        :param tagID: ID of Tag
        :param assetID: ID of Asset
        :return: Response
        This function adds a Tag to an Asset
        """
        url = self.apiurl + "/api/3/tags/" + str(tagID) + "/assets/" + str(assetID)
        response = requests.request("PUT",
                                    url,
                                    headers=self.header,
                                    verify=self.cert).json()
        return response

    def delete_asset(self, assetID):
        import requests

        url = self.apiurl + "/api/3/assets/" + str(assetID)
        return self._delete(url)
