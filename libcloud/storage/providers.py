from libcloud.storage.types import Provider

DRIVERS = {
    Provider.DUMMY:
        ('libcloud.storage.drivers.dummy', 'DummyStorageDriver'),
    Provider.CLOUDFILES_US:
        ('libcloud.storage.drivers.cloudfiles', 'CloudFilesUSStorageDriver'),
    Provider.CLOUDFILES_UK:
        ('libcloud.storage.drivers.cloudfiles', 'CloudFilesUKStorageDriver'),
}
