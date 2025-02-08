A collection of bulk operations I somewhat use for Hydrus.

Requires Python >= 3.11.

## Custom Anchor Exporting (e.g. Kemono)
```
Usage: hybt.py custom-anchor-export [OPTIONS] ANCHOR_NAME HYDRUS_QUERY

  Using your configuration defined `anchor_name`, attempts to pull relevant
  tag information from Hydrus to satisfy anchor formatting. Successfully
  created anchors will be put together into a SQLite query in
  `anchor_query.tmp`. Failed files will have their hash sent to
  `anchor_failed.tmp`.

  You will need to open your `anchor.db` with the cli tool (e.g. sqlite3) and
  copy-paste it there.

  This is meant to be used AFTER hydownloader's anchor import from Hydrus.

Arguments:
  ANCHOR_NAME   Extractor key from hydl gallery-dl-config.json  [required]
  HYDRUS_QUERY  Hydrus-advance-search-compatible tag query  [required]

Options:
  --service-name TEXT             Service name search files  [default: all
                                  local files]
  --on-deleted / --no-on-deleted  Create anchor on deleted files  [default:
                                  on-deleted]
  --help                          Show this message and exit.
```

### About Kemono/Coomer
Due to the way Kemono stores the url to files, it's near impossible to deterime the source from the url itself. Assuming you've once imported files from hydownloader in the past, hopefully you have some tags that correlate to the user id and post id.

I recommend you change the archive format from

`{service}_{user}_{id}_{filename}_{type[0]}.{extension}`

to

`{service}_{user}_{id}_{hash}`

Some creators will upload files with the same filename, which will result in conflicting anchors and will skip said files with the same filename on the same post. 

The upside with this is that you can more consistently create anchors. The downside is that (I've been told) imports might not be correctly ordered for that post. Honestly, I'm not too sure how import ordering works to be honest.
