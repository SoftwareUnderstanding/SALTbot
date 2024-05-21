import unittest
from SALTbotHandler import SALTbot
from SALTbotHandler import getMandatoryNodes
from SALTbotHandler import getOptionalNodes
import json

from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_helpers

class TestSALTbot(unittest.TestCase):
    def setUp(self):
        
        wikibase_user="SALTbot"
        wikibase_pwd="SALTbotPass"
        
        config_data = {'MEDIAWIKI_API_URL': 'http://localhost:8181/api.php', 'PASSWORD': wikibase_pwd, 'SPARQL_ENDPOINT_URL': 'http://localhost:8282/proxy/wdqs/bigdata/namespace/wdq/sparql', 'USER': wikibase_user, 'WIKIBASE_URL': 'http://localhost:8181'}
        
        if config_data['MEDIAWIKI_API_URL']!='':
            #print(config_data['MEDIAWIKI_API_URL'])
            wbi_config['MEDIAWIKI_API_URL'] = config_data['MEDIAWIKI_API_URL']
        if config_data['SPARQL_ENDPOINT_URL']!='':
            #print(config_data['SPARQL_ENDPOINT_URL'])
            wbi_config['SPARQL_ENDPOINT_URL'] = config_data['SPARQL_ENDPOINT_URL']
        if config_data['WIKIBASE_URL']!='':
            #print(config_data['WIKIBASE_URL'])
            wbi_config['WIKIBASE_URL'] = config_data['WIKIBASE_URL']

        self.wb_login_instance = wbi_login.Clientlogin(user=wikibase_user, password=wikibase_pwd)
        self.wbi = WikibaseIntegrator(login=self.wb_login_instance)
        wbi_config['USER_AGENT'] = 'MyWikibaseBot/1.0 (http://localhost/wiki/User:User)'
        
        #nodes Wikidata
        #self.man_nodes = {'instance of': 'P31', 'main subject': 'P921', 'described by source': 'P1343', 'scholarly article': 'Q13442814', 'software category': 'Q17155032', 'software': 'Q7397'}
        #self.opt_nodes = {'licenses': {'Baekmuk': 'Q116853034', 'Nunit': 'Q116853101', 'Unicode-TOU': 'Q116853475', 'CC-BY-NC-SA-2.0-DE': 'Q119146646', 'MS-LPL': 'Q119206310', 'OPL-UK-3.0': 'Q82682924', 'BUSL-1.1': 'Q121359688', 'DL-DE-ZERO-2.0': 'Q56064789', 'zlib-acknowledgement': 'Q125882644', 'LAL-1.2': 'Q152332', 'LAL-1.3': 'Q152332', 'Ruby': 'Q3066722', 'curl': 'Q33042394', 'IPA': 'Q38366264', 'APSL-1.0': 'Q621330', 'APSL-1.1': 'Q621330', 'APSL-1.2': 'Q621330', 'APSL-2.0': 'Q621330', 'SISSL': 'Q635577', 'SISSL-1.2': 'Q635577', 'Aladdin': 'Q979794', 'libtiff': 'Q105688056', 'Nokia': 'Q38495954', 'QPL-1.0': 'Q1396282', 'PSF-2.0': 'Q2600299', 'Interbase-1.0': 'Q3153096', 'SugarCRM-1.1.3': 'Q3976707', 'HPND': 'Q5773924', 'CC-BY-SA-2.5': 'Q19113751', 'CC-BY-2.5-AU': 'Q75494411', 'CC-BY-SA-3.0': 'Q14946043', 'Artistic-1.0': 'Q14624823', 'MIT': 'Q334661', 'BSD-3-Clause': 'Q18491847', 'LGPL-2.1-only': 'Q18534390', 'PostgreSQL': 'Q18563589', 'NLOD-1.0': 'Q18632926', 'CC-BY-NC-ND-3.0': 'Q19125045', 'LGPL-2.0-only': 'Q23035974', 'OLDAP-2.8': 'Q25273268', 'NTP': 'Q38495487', 'CC-BY-1.0': 'Q30942811', 'Naumen': 'Q38495690', 'NGPL': 'Q20764732', 'CC-BY-3.0-NL': 'Q53859967', 'CC-BY-SA-3.0-IGO': 'Q56292840', 'NCGL-UK-2.0': 'Q58337120', 'CC-BY-3.0-AT': 'Q75768706', 'CC-BY-SA-2.1-JP': 'Q77367349', 'MulanPSL-2.0': 'Q99634430', 'GFDL-1.1-no-invariants-or-later': 'Q103979229', 'GFDL-1.3-no-invariants-or-later': 'Q103891115', 'CC-BY-NC-ND-3.0-DE': 'Q108002189', 'AFL-2.0': 'Q108110629', 'NPL-1.1': 'Q108101156', 'AAL': 'Q38364310', 'Fair': 'Q22682017', 'OFL-1.0': 'Q113507861', 'IPL-1.0': 'Q288745', 'CERN-OHL-1.1': 'Q1023365', 'CERN-OHL-1.2': 'Q1023365', 'CERN-OHL-P-2.0': 'Q1023365', 'CERN-OHL-S-2.0': 'Q1023365', 'CERN-OHL-W-2.0': 'Q1023365', 'CECILL-1.0': 'Q1052189', 'CECILL-1.1': 'Q1052189', 'CECILL-2.0': 'Q19216649', 'CECILL-2.1': 'Q1052189', 'CECILL-B': 'Q1052189', 'CECILL-C': 'Q1052189', 'LPPL-1.0': 'Q1050635', 'LPPL-1.1': 'Q1050635', 'LPPL-1.2': 'Q1050635', 'LPPL-1.3a': 'Q1050635', 'LPPL-1.3c': 'Q1050635', 'Zlib': 'Q207243', 'Giftware': 'Q10289473', 'GPL-2.0-only': 'Q10513450', 'GPL-3.0-only': 'Q10513445', 'CC-BY-3.0-AU': 'Q52555753', 'CC-BY-SA-4.0': 'Q18199165', 'X11': 'Q18526202', 'CC-BY-2.0': 'Q19125117', 'BSD-1-Clause': 'Q19292556', 'GFDL-1.3-or-later': 'Q27019786', 'LGPL-3.0-or-later': 'Q27016762', 'EPICS': 'Q27096218', 'CATOSL-1.1': 'Q38365570', 'LiLiQ-R-1.1': 'Q38490890', 'CC-BY-ND-1.0': 'Q47008966', '0BSD': 'Q48271011', 'UCL-1.0': 'Q48795302', 'Unicode-DFS-2015': 'Q67145209', 'Unicode-DFS-2016': 'Q67145209', 'CC-BY-NC-ND-3.0-IGO': 'Q76448905', 'BSD-2-Clause-FreeBSD': 'Q90408476', 'SMLNJ': 'Q99635287', 'GFDL-1.3-invariants-only': 'Q103891111', 'GFDL-1.1-invariants-or-later': 'Q103979227', 'GFDL-1.1-no-invariants-only': 'Q103979171', 'Info-ZIP': 'Q105235524', 'CC-BY-NC-SA-3.0-IGO': 'Q106453388', 'LLVM-exception': 'Q115053236', 'Arphic-1999': 'Q115762061', 'W3C': 'Q3564577', 'Artistic-1.0-cl8': 'Q713244', 'Artistic-1.0-Perl': 'Q713244', 'Artistic-2.0': 'Q14624826', 'Libpng': 'Q6542418', 'ODbL-1.0': 'Q1224853', 'EUPL-1.0': 'Q1376919', 'EUPL-1.1': 'Q1376919', 'EUPL-1.2': 'Q123162019', 'Sleepycat': 'Q2294050', 'NCSA': 'Q2495855', 'W3C-19980720': 'Q3564577', 'W3C-20150513': 'Q3564577', 'Frameworx-1.0': 'Q5477987', 'CC-BY-2.5': 'Q18810333', 'TAPR-OHL-1.0': 'Q7669334', 'GPL-1.0-only': 'Q10513452', 'Vim': 'Q43338605', 'mpich2': 'Q17070027', 'PDDL-1.0': 'Q24273512', 'MPL-2.0': 'Q25428413', 'AGPL-1.0-only': 'Q27017230', 'GPL-3.0-or-later': 'Q27016754', 'CC-BY-ND-2.0': 'Q35254645', 'Motosoto': 'Q38494497', 'OSET-PL-2.1': 'Q38496558', 'CC-BY-NC-SA-4.0': 'Q42553662', 'OGL-Canada-2.0': 'Q56419952', 'CC-BY-NC-SA-2.0-UK': 'Q63241094', 'CC-BY-SA-2.0-UK': 'Q77365183', 'Spencer-86': 'Q97463778', 'GFDL-1.1-invariants-only': 'Q103979163', 'GFDL-1.2-no-invariants-only': 'Q103979695', 'CC-BY-NC-3.0-DE': 'Q108002180', 'JSON': 'Q125312814', 'LPL-1.02': 'Q115454534', 'ISC': 'Q386474', 'ImageMagick': 'Q27676327', 'ErlPL-1.1': 'Q3731857', 'gSOAP-1.3b': 'Q3756289', 'APL-1.0': 'Q4680711', 'NASA-1.3': 'Q6952418', 'CC-BY-SA-3.0-DE': 'Q42716613', 'CC-BY-3.0': 'Q14947546', 'LGPL-3.0-only': 'Q18534393', 'CC-BY-3.0-US': 'Q18810143', 'CC-BY-NC-2.5': 'Q19113746', 'CC-BY-SA-2.0': 'Q19068220', 'BSD-4-Clause': 'Q21503790', 'WTFPL': 'Q152481', 'MPL-1.0': 'Q26737738', 'Apache-1.0': 'Q26897902', 'GFDL-1.2-only': 'Q26921686', 'VSL-1.0': 'Q38349857', 'wxWindows': 'Q38347878', 'Entessa': 'Q38366115', 'NPOSL-3.0': 'Q38495282', 'OGTSL': 'Q38686558', 'CC-BY-NC-SA-1.0': 'Q47008954', 'CC-BY-SA-1.0': 'Q47001652', 'GFDL-1.1-or-later': 'Q50829096', 'GFDL-1.2-or-later': 'Q50829104', 'EPL-2.0': 'Q55633295', 'MIT-0': 'Q67538600', 'CC-BY-NC-SA-3.0-DE': 'Q105295756', 'IJG': 'Q106186423', 'AFL-1.1': 'Q108110597', 'MS-RL': 'Q1772828', 'w3m': 'Q116853375', 'ECL-1.0': 'Q5341236', 'ECL-2.0': 'Q5341236', 'RPL-1.1': 'Q7302458', 'RPL-1.5': 'Q7302458', 'YPL-1.0': 'Q16948289', 'YPL-1.1': 'Q16948289', 'CC-BY-ND-2.5': 'Q18810338', 'CC-BY-NC-SA-2.5': 'Q19068212', 'CC-BY-3.0-IGO': 'Q26259495', 'MPL-1.1': 'Q26737735', 'eCos-2.0': 'Q26904555', 'AGPL-3.0-or-later': 'Q27020062', 'GPL-2.0-or-later': 'Q27016752', 'CC-BY-NC-SA-2.0': 'Q28050835', 'CC-BY-NC-4.0': 'Q34179348', 'JasPer-2.0': 'Q47524112', 'SSPL-1.0': 'Q58531884', 'CC-BY-3.0-DE': 'Q62619894', 'CC-BY-SA-3.0-AT': 'Q80837139', 'OGL-UK-2.0': 'Q99891692', 'GFDL-1.2-invariants-only': 'Q103891106', 'GFDL-1.2-no-invariants-or-later': 'Q103979710', 'Elastic-2.0': 'Q104835286', 'AFL-1.2': 'Q108110612', 'CC-PDDC': 'Q114756497', 'CDLA-Permissive-2.0': 'Q115739433', 'Beerware': 'Q10249', 'BSD-2-Clause-NetBSD': 'Q191307', 'BSD-3-Clause-Attribution': 'Q191307', 'BSD-3-Clause-Clear': 'Q116978184', 'BSD-3-Clause-LBNL': 'Q191307', 'BSD-3-Clause-No-Nuclear-License': 'Q191307', 'BSD-3-Clause-No-Nuclear-License-2014': 'Q191307', 'BSD-3-Clause-No-Nuclear-Warranty': 'Q191307', 'BSD-3-Clause-Open-MPI': 'Q191307', 'BSD-4-Clause-UC': 'Q191307', 'BSD-Protection': 'Q191307', 'PHP-3.01': 'Q376841', 'CPAL-1.0': 'Q1116195', 'MirOS': 'Q1951343', 'BitTorrent-1.0': 'Q4918693', 'BitTorrent-1.1': 'Q4918693', 'D-FSL-1.0': 'Q5551105', 'CC0-1.0': 'Q6938433', 'RSCPL': 'Q7332330', 'MS-PL': 'Q15477153', 'Apache-1.1': 'Q17817999', 'CC-BY-ND-3.0': 'Q18810160', 'CC-BY-NC-ND-2.5': 'Q19068204', 'GFDL-1.1-only': 'Q26921685', 'AGPL-3.0-only': 'Q27017232', 'CDDL-1.0': 'Q26996811', 'GPL-1.0-or-later': 'Q27016750', 'CC-BY-ND-4.0': 'Q36795408', 'EUDatagrid': 'Q38365944', 'Xnet': 'Q38346089', 'LiLiQ-P-1.1': 'Q38493399', 'LiLiQ-Rplus-1.1': 'Q38493724', 'UPL-1.0': 'Q38685700', 'CC-BY-NC-1.0': 'Q44283370', 'CC-BY-NC-ND-1.0': 'Q47008926', 'MulanPSL-1.0': 'Q66563953', 'etalab-2.0': 'Q80939351', 'GCC-exception-2.0': 'Q89706542', 'CC-BY-NC-SA-2.0-FR': 'Q94507369', 'OGL-UK-1.0': 'Q99891660', 'XFree86-1.1': 'Q100375790', 'GFDL-1.3-no-invariants-only': 'Q103979743', 'gnuplot': 'Q103979882', 'NLOD-2.0': 'Q106835855', 'Intel': 'Q6043507', 'SPL-1.0': 'Q648252', 'OSL-1.0': 'Q777520', 'OSL-1.1': 'Q777520', 'OSL-2.0': 'Q777520', 'OSL-2.1': 'Q777520', 'OSL-3.0': 'Q777520', 'Classpath-exception-2.0': 'Q1486447', 'FreeBSD-DOC': 'Q2033808', 'CPL-1.0': 'Q2477807', 'ZPL-1.1': 'Q3780982', 'ZPL-2.0': 'Q3780982', 'ZPL-2.1': 'Q3780982', 'Font-exception-2.0': 'Q5514182', 'Python-2.0': 'Q5975028', 'Python-2.0.1': 'Q5975028', 'RPSL-1.0': 'Q7300815', 'Apache-2.0': 'Q13785927', 'CC-BY-NC-SA-3.0': 'Q15643954', 'EFL-1.0': 'Q17011832', 'EFL-2.0': 'Q17011832', 'CC-BY-NC-3.0': 'Q18810331', 'CC-BY-4.0': 'Q20007257', 'Unlicense': 'Q21659044', 'CDDL-1.1': 'Q26996804', 'GFDL-1.3-only': 'Q26921691', 'LGPL-2.0-or-later': 'Q27016756', 'LGPL-2.1-or-later': 'Q27016757', 'SimPL-2.0': 'Q38351460', 'CUA-OPL-1.0': 'Q38365770', 'OGDL-Taiwan-1.0': 'Q47001673', 'AGPL-1.0-or-later': 'Q54571707', 'EPL-1.0': 'Q55633170', 'Multics': 'Q38494754', 'GFDL-1.3-invariants-or-later': 'Q103979768', 'NPL-1.0': 'Q108101155', 'OFL-1.1': 'Q113507844', 'OpenSSL': 'Q89948816', 'OPUBL-1.0': 'Q1412537', 'BSL-1.0': 'Q2353141', 'CPOL-1.02': 'Q5140041', 'Watcom-1.0': 'Q7659488', 'CC-BY-NC-ND-4.0': 'Q24082749', 'ODC-By-1.0': 'Q30940585', 'CNRI-Python': 'Q38365646', 'OCLC-2.0': 'Q38496210', 'CC-BY-NC-2.0': 'Q44128984', 'CC-BY-NC-ND-2.0': 'Q47008927', 'FDK-AAC': 'Q47524122', 'DL-DE-BY-2.0': 'Q64859812', 'Zend-2.0': 'Q85269786', 'OGL-UK-3.0': 'Q99891702', 'GFDL-1.2-invariants-or-later': 'Q103891130', 'CC-BY-ND-3.0-DE': 'Q108002236', 'AFL-2.1': 'Q108110640', 'AFL-3.0': 'Q108111552', 'LPL-1.0': 'Q115454512', 'Abstyles': 'Q116852450', 'AdaCore-doc': 'Q116852532', 'ANTLR-PD': 'Q116853028'}, 'code repository': 'P1324', 'programming language': 'P277', 'download url': None, 'license': 'P275', 'version control system': 'P8423', 'web interface software': 'P10627', 'Git': 'Q58219900', 'GitHub': 'Q45767371', 'DOI': 'P356', 'free software': 'Q341'}

        #self.man_nodes = getMandatoryNodes(self.wbi, config_data)
        #self.opt_nodes = getOptionalNodes(self.wbi, config_data)
        
        self.man_nodes = {'instance of': 'P32', 'main subject': 'P238', 'described by source': 'P187', 'scholarly article': 'Q86', 'software category': 'Q22', 'software': 'Q7'}
        self.opt_nodes = {'licenses': {}, 'code repository': 'P174', 'programming language': None, 'download url': None, 'license': None, 'version control system': 'P175', 'web interface software': 'P176', 'Git': 'Q63', 'GitHub': 'Q64', 'DOI': 'P242', 'free software': 'Q3'}

        
        #print('man_nodes: ', self.man_nodes)
        #print('opt_nodes: ', self.opt_nodes)

        
        self.pytorch = open('/home/j/SALTbot/SALTbot/src/SALTbot/test_data/Pytorch.json', 'r')
        self.pytorch_data = json.loads(self.pytorch.read())
        self.widoco = open('/home/j/SALTbot/SALTbot/src/SALTbot/test_data/Widoco.json', 'r')
        self.widoco_data = json.loads(self.widoco.read())
        self.somef = open('/home/j/SALTbot/SALTbot/src/SALTbot/test_data/somef.json', 'r')
        self.somef_data = json.loads(self.somef.read())
        #print(self.pytorch_data)
    #man_nodes = SALTbotHandler.getMandatoryNodes(wbi, config_data)
    def tearDown(self):
        self.pytorch.close()
        self.widoco.close()
        self.somef.close()
    '''    
    def test_SALTbot_1(self):
        "This test checks SALTbot behaviour when both articles and software are in the wikibase"
        results = SALTbot(self.wbi, self.pytorch_data, self.man_nodes, self.opt_nodes, True, {})
        #results = open('/home/j/SALTbot/SALTbot/src/SALTbot/operation_list.txt', 'r')
        self.assertEqual(results, [])
    '''  
    '''
    def test_SALTbot_2(self):
        "This test checks SALTbot behaviour when software is missing in the wikibase"
        results = SALTbot(self.wbi, self.widoco_data, self.man_nodes, self.opt_nodes, False, {})
        #results = open('/home/j/SALTbot/SALTbot/src/SALTbot/operation_list.txt', 'r')
        #print('results', results)
        
        #crea Widoco
        self.assertEqual(results[0], ['create', {'LABEL': 'Widoco', 'DESCRIPTION': 'Wizard for documenting ontologies. WIDOCO is a step by step generator of HTML templates with the documentation of your ontology. It uses the LODE environment to create part of the template.'}])
        #Crea statement URL 
        self.assertEqual(results[1][0], 'statement')
        self.assertEqual(results[1][1]['datatype'], 'URL')
        self.assertEqual(results[1][1]['s'], 'Widoco')
        self.assertEqual(results[1][1]['p'], self.opt_nodes['code repository'])
        self.assertEqual(results[1][1]['o'], 'https://github.com/dgarijo/Widoco')
        
        #crea statement instance of software
        self.assertEqual(results[2][0], 'statement')
        self.assertEqual(results[2][1]['datatype'], 'Item')
        self.assertEqual(results[2][1]['s'], 'Widoco')
        self.assertEqual(results[2][1]['p'], self.man_nodes['instance of'])
        self.assertEqual(results[2][1]['o'], self.man_nodes['software'])
        
        #crea enlace software-articulo
        self.assertEqual(results[3][0], 'statement')
        self.assertEqual(results[3][1]['datatype'], 'Item')
        self.assertEqual(results[3][1]['s'], 'Widoco')
        self.assertEqual(results[3][1]['p'], self.man_nodes['described by source'])
        self.assertEqual(results[3][1]['o'], 'Q124')
        
        #crea enlace articulo-software
        self.assertEqual(results[4][0], 'statement')
        self.assertEqual(results[4][1]['datatype'], 'Item')
        self.assertEqual(results[4][1]['s'], 'Q124')
        self.assertEqual(results[4][1]['p'], self.man_nodes['main subject'])
        self.assertEqual(results[4][1]['o'], 'Widoco')
    '''
    def test_SALTbot_3(self):
        "This test checks SALTbot behaviour when software and articles are missing in the wikibase"
        results = SALTbot(self.wbi, self.somef_data, self.man_nodes, self.opt_nodes, False, {})
        #results = open('/home/j/SALTbot/SALTbot/src/SALTbot/operation_list.txt', 'r')
        #print('results', results)
        
        #crea somef articulo
        self.assertEqual(results[0], ['create', {'LABEL': 'somef scholarly article', 'DESCRIPTION': 'SOftware Metadata Extraction Framework: A tool for automatically extracting relevant software information from readme files'}])
        
        #FALTA CREA INSTANCE OF ARTICULO
        
        #crea somef software
        self.assertEqual(results[1], ['create', {'LABEL': 'somef', 'DESCRIPTION': 'SOftware Metadata Extraction Framework: A tool for automatically extracting relevant software information from readme files'}])
        
        
        #Crea statement URL 
        self.assertEqual(results[2][0], 'statement')
        self.assertEqual(results[2][1]['datatype'], 'URL')
        self.assertEqual(results[2][1]['p'], self.opt_nodes['code repository'])
        self.assertEqual(results[2][1]['o'], 'https://github.com/KnowledgeCaptureAndDiscovery/somef')
        
        #crea statement instance of software
        self.assertEqual(results[3][0], 'statement')
        self.assertEqual(results[3][1]['datatype'], 'Item')
        self.assertEqual(results[3][1]['s'], 'somef')
        self.assertEqual(results[3][1]['p'], self.man_nodes['instance of'])
        self.assertEqual(results[3][1]['o'], self.man_nodes['software'])
        
        #crea enlace software-articulo
        self.assertEqual(results[4][0], 'statement')
        self.assertEqual(results[4][1]['datatype'], 'Item')
        self.assertEqual(results[4][1]['s'], 'somef')
        self.assertEqual(results[4][1]['p'], self.man_nodes['described by source'])
        self.assertEqual(results[4][1]['o'], 'somef scholarly article')
        
        #crea enlace articulo-software
        self.assertEqual(results[5][0], 'statement')
        self.assertEqual(results[5][1]['datatype'], 'Item')
        self.assertEqual(results[5][1]['s'], 'somef scholarly article')
        self.assertEqual(results[5][1]['p'], self.man_nodes['main subject'])
        self.assertEqual(results[5][1]['o'], 'somef')
    