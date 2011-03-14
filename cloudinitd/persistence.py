import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relation
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table
from sqlalchemy import Integer
from sqlalchemy import String, MetaData, Sequence
from sqlalchemy import Column
import ConfigParser
from sqlalchemy import types
from datetime import datetime
import os
import cloudinitd
from cloudinitd.exceptions import APIUsageException


__author__ = 'bresnaha'

metadata = MetaData()


def config_get_or_none(parser, s, v, default=None):
    try:
        x = parser.get(s, v)
        if not x:
            return x
        x = cloudinitd.get_env_val(x)
        return x
    except:
        return default


boot_table = Table('boot', metadata,
    Column('id', Integer, Sequence('event_id_seq'), primary_key=True),
    Column('topconf', String(1024)),
    Column('timestamp', types.TIMESTAMP(), default=datetime.now()),
    Column('status', Integer),
    )

level_table = Table('level', metadata,
    Column('id', Integer, Sequence('event_id_seq'), primary_key=True),
    Column('order', Integer),
    Column('conf_file', String(1024)),
    Column('name', String(64)),
    Column('boot_id', Integer, ForeignKey('boot.id'))
    )

service_table = Table('service', metadata,
    Column('id', Integer, Sequence('event_id_seq'), primary_key=True),
    Column('name', String(64)),
    Column('level_id', Integer, ForeignKey('level.id')),
    Column('image', String(32)),
    Column('iaas', String(32)),
    Column('allocation', String(64)),
    Column('keyname', String(32)),
    Column('localkey', String(1024)),
    Column('username', String(32)),
    Column('scp_username', String(32)),
    Column('readypgm', String(1024)),
    Column('hostname', String(64)),
    Column('bootconf', String(1024)),
    Column('bootpgm', String(1024)),
    Column('securitygroups', String(1024)),
    Column('deps', String(1024)),
    Column('instance_id', String(64)),
    Column('iaas_hostname', String(64)),
    Column('iaas_port', Integer),
    Column('iaas_key', String(64)),
    Column('iaas_secret', String(64)),    
    Column('contextualized', Integer, default=0),
    Column('last_error', sqlalchemy.types.Text()),
    Column('terminatepgm', String(1024)),
    )

attrbag_table = Table('attrbag', metadata,
    Column('id', Integer, Sequence('extra_id_seq'), primary_key=True),
    Column('key', String(50)),
    Column('value', String(50)),
    Column('service_id', Integer, ForeignKey('service.id'))
    )


def _resolve_file_or_none(context_dir, conf, conf_file):
    """Return absolute path to file if specified.  If None or empty string return None.

    Supports configurations of "../xyz" (or "xyz") being taken relative to the configuration
    file it was specified in.

    * context_dir - Directory of the configuration file (level*conf)

    * conf - Configuration value, may be None or empty string

    * conf_file - Absolute path to the file where the configuration was (for errors)

    If there is a path to be resolved, Exception is raised when it does not exist.
    """
    if not conf:
        return None
    base1 = os.path.expanduser(context_dir)
    base2 = os.path.expanduser(conf)
    path = os.path.join(base1, base2)
    path = os.path.abspath(path) # This resolves "/../"
    if not os.path.exists(path):
        raise Exception("File does not exist: '%s'.  This was "
                        "referenced in the file '%s'." % (path, conf_file))
    return path

class BootObject(object):

    def __init__(self, topconf):
        self.topconf = topconf
        self.status = 0
        self.levels = []

class LevelObject(object):

    def __init__(self, conf_file, name, order):
        self.conf_file = conf_file
        self.name = name
        self.order = order


class ServiceObject(object):

    def __init__(self):
        # all of the db backed variables
        self.id = None
        self.name = None
        self.level_id = None
        self.image = None
        self.iaas = None
        self.allocation = None
        self.keyname = None
        self.localkey = None
        self.username = None
        self.scp_username = None
        self.readypgm = None
        self.hostname = None
        self.bootconf = None
        self.bootpgm = None
        self.instance_id = None
        self.iaas_hostname = None
        self.iaas_port = None
        self.iaas_key = None
        self.iaas_secret = None
        self.contextualized = 0
        self.securitygroups = None

    def _load_from_conf(self, parser, section, db, conf_dir, cloud_confs, conf_file):
        """conf_dir is the directory of the particular level*conf file"""

        iaas = config_get_or_none(parser, section, "iaas")
        iaas_hostname = config_get_or_none(parser, section, "iaas_hostname")

        sshkey = config_get_or_none(parser, section, "sshkeyname")
        localssh = config_get_or_none(parser, section, "localsshkeypath")
        ssh_user = config_get_or_none(parser, section, "ssh_username")
        scp_user = config_get_or_none(parser, section, "scp_username")
        bootconf = config_get_or_none(parser, section, "bootconf")
        bootpgm = config_get_or_none(parser, section, "bootpgm")
        hostname = config_get_or_none(parser, section, "hostname")
        readypgm = config_get_or_none(parser, section, "readypgm")
        iaas_key = config_get_or_none(parser, section, "iaas_key")
        iaas_secret = config_get_or_none(parser, section, "iaas_secret")
        securitygroups = config_get_or_none(parser, section, "securitygroups")

        allo = config_get_or_none(parser, section, "allocation")
        image = config_get_or_none(parser, section, "image")
        cloudconf = config_get_or_none(parser, section, "cloud")
        if cloudconf:
            try:
                conf = cloud_confs[cloudconf]
            except:
                raise APIUsageException("%s is not a valud cloud description in this plan" % (cloudconf))

            if not iaas:
                iaas = conf.iaas
            if not iaas_hostname:
                iaas_hostname = conf.iaas_hostname
            if not sshkey:
                sshkey = conf.sshkey
            if not localssh:
                localssh = conf.localssh
            if not ssh_user:
                ssh_user = conf.ssh_user
            if not scp_user:
                scp_user = conf.scp_user
            if not iaas_key:
                iaas_key = conf.iaas_key
            if not iaas_secret:
                iaas_secret = conf.iaas_secret
            if not securitygroups:
                securitygroups = conf.securitygroups

        if not iaas:
            iaas = db.default_iaas
        if not iaas_hostname:
            iaas_hostname = db.default_iaas_hostname
        if not allo:
            allo = db.default_allo
        if not sshkey:
            sshkey = db.default_sshkey
        if not localssh:
            localssh = db.default_localssh
        if not ssh_user:
            ssh_user = db.default_ssh_user
        if not scp_user:
            scp_user = db.default_scp_user
        if not iaas_key:
            iaas_key = db.default_iaas_key
        if not iaas_secret:
            iaas_secret = db.default_iaas_secret
        if not securitygroups:
            securitygroups = db.default_securitygroups

        self.name = section.replace("svc-", "")
        self.image = image
        self.bootconf = _resolve_file_or_none(conf_dir, bootconf, conf_file)
        self.bootpgm = _resolve_file_or_none(conf_dir, bootpgm, conf_file)
        self.hostname = hostname
        self.readypgm = _resolve_file_or_none(conf_dir, readypgm, conf_file)
        self.username = ssh_user
        self.scp_username = scp_user
        self.localkey = _resolve_file_or_none(conf_dir, localssh, conf_file)
        self.keyname = sshkey
        self.allocation = allo
        self.iaas = iaas
        self.iaas_hostname = iaas_hostname

        self.iaas_secret = iaas_secret
        self.iaas_key = iaas_key
        self.securitygroups = securitygroups

        item_list = parser.items(section)
        deps_list = []
        for (ka,val) in item_list:
            ndx = ka.find("deps")
            if ndx == 0:
                deps_list.append(ka)
        deps_list.sort()
        for i in deps_list:
            deps = config_get_or_none(parser, section, i)
            deps_file = _resolve_file_or_none(conf_dir, deps, conf_file)
            if deps_file:
                parser2 = ConfigParser.ConfigParser()
                parser2.read(deps_file)
                keys_val = parser2.items("deps")
                for (ka,val) in keys_val:
                    bao = BagAttrsObject(ka, val)
                    self.attrs.append(bao)
            

                
class BagAttrsObject(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value

mapper(BagAttrsObject, attrbag_table)
mapper(ServiceObject, service_table, properties={
    'attrs': relation(BagAttrsObject)})
mapper(LevelObject, level_table, properties={
    'services': relation(ServiceObject)})
mapper(BootObject, boot_table, properties={
    'levels': relation(LevelObject)})

class CloudConfSection(object):

    def __init__(self, parser, section):

        self.name = section
        self.iaas = config_get_or_none(parser, section, "iaas")
        self.sshkey = config_get_or_none(parser, section, "sshkeyname")
        self.localssh = config_get_or_none(parser, section, "localsshkeypath")
        self.ssh_user = config_get_or_none(parser, section, "ssh_username")
        self.scp_user = config_get_or_none(parser, section, "scp_username")
        self.iaas_hostname = config_get_or_none(parser, section, "iaas_hostname")
        self.iaas_port = config_get_or_none(parser, section, "iaas_port", 8444)
        self.iaas_key = config_get_or_none(parser, section, "iaas_key")
        self.iaas_secret = config_get_or_none(parser, section, "iaas_secret")
        self.securitygroups = config_get_or_none(parser, section, "securitygroups")


class CloudInitDDB(object):

    def __init__(self, dburl, module=None):

        self._cloudconf_sections = {}

        if module == None:
            self._engine = sqlalchemy.create_engine(dburl)
        else:
            self._engine = sqlalchemy.create_engine(dburl, module=module)
        metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)
        self._session = self._Session()


    def db_obj_add(self, obj):
        self._session.add(obj)

    def db_commit(self):
        self._session.commit()

    def load_from_db(self):
        bo = self._session.query(BootObject).first()
        return bo

    def load_from_conf(self, conf_file):
        conf_file = os.path.abspath(conf_file)
        parser = ConfigParser.ConfigParser()

        self._confdir = os.path.abspath(os.path.dirname(conf_file))
        if not os.path.exists(self._confdir):
            raise APIUsageException("the path %s does not exist" % (self._confdir))
        conf_file = os.path.join(self._confdir, conf_file)
        if not os.path.exists(conf_file):
            raise APIUsageException("the path %s does not exist" % (conf_file))
        parser.read(conf_file)

        # get the system defaults
        s = "defaults"
        self.default_iaas = config_get_or_none(parser, s, "iaas")
        self.default_allo = config_get_or_none(parser, s, "allocation")
        self.default_sshkey = config_get_or_none(parser, s, "sshkeyname")
        self.default_localssh = config_get_or_none(parser, s, "localsshkeypath")
        self.default_ssh_user = config_get_or_none(parser, s, "ssh_username")
        self.default_scp_user = config_get_or_none(parser, s, "scp_username")
        self.default_iaas_hostname = config_get_or_none(parser, s, "iaas_hostname")
        self.default_iaas_port = config_get_or_none(parser, s, "iaas_port", 8444)
        self.default_iaas_key = config_get_or_none(parser, s, "iaas_key")
        self.default_iaas_secret = config_get_or_none(parser, s, "iaas_secret")
        self.default_securitygroups = config_get_or_none(parser, s, "securitygroups")

#        iaas_hostname = config_get_or_none(parser, section, "iaas_hostname")
#        bootconf = config_get_or_none(parser, section, "bootconf")
#        bootpgm = config_get_or_none(parser, section, "bootpgm")
#        hostname = config_get_or_none(parser, section, "hostname")
#        readypgm = config_get_or_none(parser, section, "readypgm")
#        image = config_get_or_none(parser, section, "image")
#        cloudconf = config_get_or_none(parser, section, "cloud")



        all_sections = parser.sections()
        for s in all_sections:
            ndx = s.find("cloud-")
            if ndx == 0:
                cloudconf = CloudConfSection(parser, s)
                self._cloudconf_sections[s] = cloudconf
        

        lvl_dict = {}
        levels = parser.items("runlevels")
        for l in levels:
            (key, val) = l

            # if the key has the word level in it we do something otherwise we log a warning
            ndx = key.find("level")
            if ndx == 0:
                level_file = os.path.join(self._confdir, val)
                (level, order) = self.build_level(key, level_file)
                lvl_dict[order] = level

        bo = BootObject(conf_file)
        lvl_dict.keys().sort()
        for k in lvl_dict.keys():
            lvl = lvl_dict[k]
            self._session.add(lvl)
            bo.levels.append(lvl)

        self._session.add(bo)
        self._session.commit()
        self.bo = bo
        return bo

    
    def build_level(self, level_name, level_file):
        parser = ConfigParser.ConfigParser()
        parser.read(level_file)

        sections = parser.sections()

        context_dir = os.path.dirname(level_file)

        order = int(level_name.replace("level", ""))
        level = LevelObject(level_file, level_name, order)
        for s in sections:
            ndx = s.find("svc-")
            if ndx == 0:
                svc_db = ServiceObject()
                svc_db._load_from_conf(parser, s, self, context_dir, self._cloudconf_sections, level_file)
                level.services.append(svc_db)
                self._session.add(svc_db)
        return (level, order)



