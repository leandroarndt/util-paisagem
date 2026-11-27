from tkinter import messagebox
import webbrowser
from github3 import GitHub
from github3.repos import Repository
from github3.repos.release import Release
from utilpaisagem.app_info import string_version

class Tag(object):
    """Comparable tags"""
    version:int
    subversion:int
    revision:int
    rc:int
    
    def __init__(self, tag:str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tag = tag.strip('v')
        self.version, self.subversion, self.revision = tag.split('.')
        if 'rc' in self.revision:
            self.revision, self.rc = self.revision.split('rc')
        else:
            self.rc = 0
    
    def __gt__(self, other)->bool:
        if not isinstance(other, Tag):
            raise NotImplemented
        if not (other.rc or self.rc):
            if self.version > other.version:
                return True
            if self.version == other.version:
                if self.subversion > other.subversion:
                    return True
                if self.subversion == other.subversion and self.revision > other.revision:
                    return True
            return False
        if self.rc and other.rc:
            if self.version > other.version:
                return True
            if self.version == other.version:
                if self.subversion > other.subversion:
                    return True
                if self.subversion == other.subversion:
                    if self.revision > other.revision:
                        return True
                    if self.revision == other.revision and self.rc > other.rc:
                        return True
            return False
        if other.rc and not self.rc: 
            return True # Attention: leads to unbiguous results! Always do current > github release
        if self.rc and not other.rc:
            if self.version > other.version:
                return True
            if self.version == other.version and self.subversion > other.subversion:
                return True
            if self.version == other.version and self.subversion == other.subversion \
                and self.revision > other.revision:
                return True
            else:
                return False
        return False
    
    def __eq__(self, other)->bool:
        if not isinstance(other, Tag):
            raise NotImplemented
        if self.version == other.version and self.subversion == other.subversion and \
            self.revision == other.revision and self.rc == other.rc:
            return True
        return False
    
    def __ge__(self, other)->bool:
        if self > other or self == other:
            return True
        return False
    
    def __lt__(self, other)->bool:
        if self == other or self > other:
            return False
        return True

    def __le__(self, other)->bool:
        if self == other or self < other:
            return True
        return False
    
    def __str__(self)->str:
        return f'v{self.version}.{self.subversion}.{self.revision}{f"rc{self.rc}" if self.rc else ""}'

    def __repr__(self) -> str:
        return f'Tag("v{self.version}.{self.subversion}.{self.revision}{f"rc{self.rc}" if self.rc else ""}")'

class Upgrader(object):
    """Blocking package upgrader. Should be run in another process.
    """
    anonymous:GitHub
    repository:Repository
    current:Tag
    newest:Release
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current = Tag(
            f'v{string_version()}'
        )
        try:
            self.anonymous = GitHub()
            self.repository = self.anonymous.repository('leandroarndt', 'util-paisagem')
        except:
            print('Could not connect to Github.')
    
    def run(self):
        print(f'Running version {self.current}')
        try:
            releases = self.repository.releases()
        except:
            print('Could not retrieve releases from Github.')
            return
        newest_tag = Tag('v0.0.0')
        for r in releases:
            if Tag(r.tag_name) > newest_tag:
                newest_tag = Tag(r.tag_name)
                self.newest = r
        if self.current >= newest_tag:
            print('Newest version already installed.')
        else:
            print(f'Found new version {newest_tag}.')
            if messagebox.askokcancel(
                title=_('New version found!'),
                message=_(
                    'There is a new Útil paisagem version available ({newest_tag}). Open download page?'
                ).format(newest_tag=newest_tag)
            ):
                webbrowser.open(self.newest.html_url)