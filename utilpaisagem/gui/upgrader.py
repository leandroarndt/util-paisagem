from tkinter import messagebox
import webbrowser, requests, tempfile
from zipfile import ZipFile
from queue import Queue
from github3 import GitHub
from github3.repos import Repository
from github3.repos.release import Release
from github3.exceptions import NotFoundError, ForbiddenError
from utilpaisagem.app_info import string_version, translations_path
from utilpaisagem.gui.common import format_status, Settings

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
    github:GitHub
    repository:Repository
    current:Tag
    newest:Release
    upstream_queue:Queue
    settings:Settings
    
    def __init__(self, upstream_queue:Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.upstream_queue = upstream_queue
        self.current = Tag(
            f'v{string_version()}'
        )
        self.settings = Settings()
        try:
            self.github = GitHub()
            self.repository = self.github.repository('leandroarndt', 'util-paisagem')
        except ForbiddenError as e:
            self.upstream_queue.put_nowait(format_status(
                _('Github forbide connection ({e}).').format(e=e),
                self,
            ))
            self.github = None
            self.repository = None
        except Exception as e:
            self.upstream_queue.put_nowait(format_status(
                _('Could not connect to Github ({e}).').format(e=e),
                self,
            ))
            self.github = None
            self.repository = None
    
    def run(self):
        if self.github is None:
            return

        print(f'Running version {self.current}')

        # Check for Útil paisagem upgrades
        try:
            releases = self.repository.releases()
        except ForbiddenError as e:
            self.upstream_queue.put_nowait(format_status(
                _('Github forbide access to release list ({e}).').format(e=e),
                self,
            ))
        except Exception as e:
            self.upstream_queue.put_nowait(format_status(
                _('Could not retrieve releases from Github ({e}).').format(e=e),
                self,
            ))
            return
        newest_tag = Tag('v0.0.0')
        try:
            for r in releases:
                if Tag(r.tag_name) > newest_tag:
                    newest_tag = Tag(r.tag_name)
                    self.newest = r
            if self.current >= newest_tag:
                self.upstream_queue.put_nowait(format_status(
                    _('Newest version already installed.'),
                    self,
                ))
            else:
                self.upstream_queue(format_status(
                    _('Found new version {newest_tag}.').format(newest_tag=newest_tag),
                    self,
                ))
                if messagebox.askokcancel(
                    title=_('New version found!'),
                    message=_(
                        'There is a new Útil paisagem version available ({newest_tag}). Open download page?'
                    ).format(newest_tag=newest_tag)
                ):
                    webbrowser.open(self.newest.html_url)
        except ForbiddenError as e:
            self.upstream_queue.put_nowait(format_status(
                _('Github forbade retrieving information on a release ({e}).').format(e),
                self,
            ))
        except Exception as e:
            self.upstream_queue.put_nowait(format_status(
                _('Could not retrieve release info from Github ({e}).').format(e),
                self,
            ))

        # Check for translation updates
        if self.settings.download_translations:
            try:
                current = self.repository.release_from_tag(f'v{string_version()}')
            except NotFoundError:
                self.upstream_queue.put_nowait(format_status(
                    _('Could not find release for current version ({string_version}).').format(
                        string_version=string_version(),
                    ),
                    self,
                ))
            except ForbiddenError as e:
                self.upstream_queue.put_nowait(format_status(
                    _('Github forbade getting information for current release ({e}).').format(e),
                    self,
                ))
            except Exception as e:
                self.upstream_queue.put_nowait(format_status(
                    _('Could not connect to Github ({e}).').format(e),
                    self,
                ))
            else:
                try:
                    assets = current.assets()
                    for a in assets:
                        if a.name == 'translations.zip':
                            if (translations_path.parent / 'translations.sha').exists():
                                with open(translations_path.parent / 'translations.sha', 'r') as digest:
                                    if a.digest == digest.read():
                                        self.upstream_queue.put_nowait(format_status(
                                            _('Most recent translations already installed.'),
                                            self,
                                        ))
                                        return
                            self.upstream_queue.put_nowait(format_status(
                                _('Downloading most recent translations...'),
                                self,
                            ))
                            r = requests.get(a.browser_download_url)
                            if r.status_code == 200:
                                with tempfile.TemporaryFile('wb+') as temp:
                                    temp.write(r.content)
                                    ziptemp = ZipFile(temp)
                                    ziptemp.extractall(translations_path)
                                self.upstream_queue.put_nowait(format_status(
                                    _('Translations updated. Will take effect after Útil paisagem restarts.'),
                                    self,
                                ))
                                with open(translations_path.parent / 'translations.sha', 'w') as digest:
                                    digest.write(a.digest)
                            else:
                                self.upstream_queue.put_nowait(format_status(
                                    _('Could not download new translations. Request returned code {code}.').format(
                                        code=r.status_code,
                                    ),
                                    self,
                                ))
                except ForbiddenError as e:
                    self.upstream_queue.put_nowait(format_status(
                        _('Github forbade accessing information on release asset ({e}).').format(e=e),
                        self
                    ))
                except Exception as e:
                    self.upstream_queue.put_nowait(format_status(
                        _('Could not retrieve information on release asset ({e}).').format(e=e),
                        self
                    ))
        else:
            self.upstream_queue.put_nowait(format_status(
                _('Skipping check for new translations due to user preferences.'),
                self,
            ))
