#### Weirdness with PIL and pillow

So apparently, if you are not running in a virtual environment, pil and or
pillow do not work.

So, one can only run this file by first entering `$ pipenv shell`

Secondly, they only work as imported via:

```python
import PIL as pillow
from pillow import Image
```

Nope. That way no longer works.

```python
from PIL import Image
```

Thirdly, `pillow` must be installed `$ pipenv insall pillow` and called as `PIL`

ha-larious

This all has to do with a whole bunch of goofyness which can be found
(here)[https://stackoverflow.com/questions/49247310/no-module-named-pil]:
