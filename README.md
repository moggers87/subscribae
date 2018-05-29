

# subscribae project

Organise your Youtube subscriptions into something sane

The main idea is that a user can assign their subscriptions to "buckets" and
those "buckets" will get filled up with videos. For a Youtube user who is
subscribed to a large and diverse number of channels, it can be tiresome
organising videos to the point of it becoming a chore.

Eventually you give up and interesting science videos get lost between a few
gaming channels publishing their invidual perspectives on a recent multiplayer
match.

If only the auto-playlist feature allowed adding rules based on channels!

## Common issues

### ImportError

If you get something like this:

```
ImportError: No module named appengine
```

That means you have another package installed that uses `google` as it's parent
package, e.g. protobuf. The App Engine SDK is rather unfriendly as it doesn't
implement PEP 420 and so conflicts. The suggested workaround is to create an
empty virtualenv and use that to isolate the SDK from globally installed
packages.

### IOError

This started to appear once Subscribae was updated to SDK version 1.9.57 if
pytz was installed globally. The suggested workaround is to create an empty
virtualenv and use that to isolate the SDK from globally installed packages.

## Licenses

Subscribae is licensed under the terms of the GPLv3.

Sibuscribae used
[djangae-scaffold](https://github.com/potatolondon/djangae-scaffold) as a
template, which is licensed under the terms of the Apache License, version 2.0.
