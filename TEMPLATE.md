Composing Templates
===================

Templates are simple ODT documents. You can create them using Writer.
An OpenDocument file is basically a ZIP archive containing some XML files. If
you plan to use control flow or conditionals it is a good idea to familiarise
yourself a little bit with the OpenDocument XML to understand better what's
going on behind the scenes.

## Printing Variables

Since Secretary use the same template syntax of Jinja2, to print a varible type
a double curly braces enclosing the variable, like so:
```jinja
    {{ foo.bar }}
    {{ foo['bar'] }}
```

However, mixing template instructions and normal text into the template
document may become confusing and clutter the layout and most important, in
most cases will produce invalid ODT documents. Secretary recommends using an
alternative way of inserting fields. Insert a visual field in LibreOffice
Writer from the menu `Insert` > `Fields` > `Other...` (or just press
`Ctrl+F2`), then click on the `Functions` tab and select `Input field`. Click
`Insert`. A dialog will appear where you can insert the print instructions. You
can even insert simple control flow tags to dynamically change what is printed
in the field.

Secretary will handle multiline variable values replacing the line breaks with
a `<text:line-break/>` tag.

## Control Flow

Most of the time secretary will handle the internal composing of XML when you
insert control flow tags (`{% for foo in foos %}`, `{% if bar %}`, etc and its
enclosing tags. This is done by finding the present or absence of other
secretary tags within the internal XML tree.

### Examples document structures

**Printing multiple records in a table**

![alt tag](https://raw.githubusercontent.com/christopher-ramirez/secretary/development/docs/images/table_01.png)

**Conditional paragraphs**

![alt tag](https://raw.githubusercontent.com/christopher-ramirez/secretary/development/docs/images/conditional_paragraph_01.png)

The last example could had been simplified into a single paragraph in Writer
like:
```jinja
{% if already_paid %}YOU ALREADY PAID{% else %}YOU HAVEN'T PAID{% endif %}
```

**Printing a list of names**
```jinja
{% for name in names %}
    {{ name }}
{% endfor %}
```

Automatic control flow in Secretary will handle the intuitive result of the
above examples and similar thereof.

Although most of the time the automatic handling of control flow in secretary
may be good enough, we still provide an additional method for manual control of
the flow. Use the `reference` property of the field to specify where where the
control flow tag will be used or internally moved within the XML document:

* `paragraph`: Whole paragraph containing the field will be replaced with the
  field content.
* `before::paragraph`: Field content will be moved before the current
  paragraph.
* `after::paragraph`: Field content will be moved after the current paragraph.
* `row`: The entire table row containing the field will be replace with the
  field content.
* `before::row`: Field content will be moved before the current table row.
* `after::row`: Field content will be moved after the current table row.
* `cell`: The entire table cell will be replaced with the current field
  content. Even though this setting is available, it is not recommended.
  Generated documents may not be what you expected.
* `before::cell`: Same as `before::row` but for a table cell.
* `after::cell`: Same as `after::row` but for a table cell.
> Field content is the control flow tag you insert with the Writer *input field*

## Hyperlink  Support

LibreOffice by default escapes every URL in links, pictures or any other
element supporting hyperlink functionallity. This can be a problem if you need
to generate dynamic links because your template logic is URL encoded and
impossible to be handled by the Jinja engine. Secretary solves this problem by
reserving the `secretary` URI scheme. If you need to create dynamic links in
your documents, prepend every link with the `secretary:` scheme.

So for example if you have the following dynamic link:
`https://mysite/products/{{ product.id }}`, prepend it with the
**`secretary:`** scheme, leaving the final link as
`secretary:https://mysite/products/{{ product.id }}`.

## Image Support
Secretary allows you to use placeholder images in templates that will be
replaced when rendering the final document. To create a placeholder image on
your template:

1. Insert an image into the document as normal. This image will be replaced
   when rendering the final document.
2. Change the name of the recently added image to a Jinja2 print tag (the ones
   with double curly braces). The variable should call the `image` filter,
   i.e.: Suppose you have a client record (passed to template as `client`
   object), and a picture of him is stored in the `picture` field. To print the
   client's picture into a document set the image name to `{{
   client.picture|image }}`.

> To change image name, right click under image, select "Picture..." from the
> popup menu and navigate to "Options" tab.

### Media loader

To load image data, Secretary needs a media loader. The engine by default
provides a file system loader which takes the variable value (specified in
image name). This value can be a file object containing an image or an absolute
or a relative filename to `media_path` passed at `Renderer` instance creation.

Since the default media loader is very limited. Users can provide theirs own
media loader to the `Renderer` instance. A media loader can perform image
retrieval and/or any required transformation of images. The media loader must
take the image value from the template and return a tuple whose first item is a
file object containing the image. Its second element must be the image
mimetype.

Example declaring a media loader:
```python
    from secretary import Renderer

    engine = Renderer()

    @engine.media_loader
    def db_images_loader(value, *args, *kwargs):
        # load from images collection the image with `value` id.
        image = db.images.findOne({'_id': value})

        return (image, the_image_mimetype)

    engine.render(template, **template_vars)
```
The media loader also receive any argument or keywork arguments declared in the
template. i.e: If the placeholder image's name is: `{{
client.image|image('keep_ratio', tiny=True)}}` the media loader will receive:
first the value of `client.image` as it first argument; the string `keep_ratio`
as an additional argument and `tiny` as a keyword argument.

The loader can also access and update the internal `draw:frame` and
`draw:image` nodes. The loader receives as a dictionary the attributes of these
nodes through `frame_attrs` and `image_attrs` keyword arguments. Is some update
is made to these dictionary secretary will update the internal nodes with the
changes. This is useful when the placeholder's aspect radio and replacement
image's aspect radio are different and you need to keep the aspect ratio of the
original image.

## Builtin Filters
Secretary includes some predefined *jinja2* filters. Included filters are:

- **image(value)**
See *Image Support* section above.

- **markdown(value)**
Convert the value, a markdown formated string, into a ODT formated text. Example:

        {{ invoice.description|markdown }}

- **pad(value, length)**
Pad zeroes to `value` to the left until output value's length be equal to
`length`. Default length if 5. Example:

        {{ invoice.number|pad(6) }}

## Features of jinja2 not supported

Secretary supports most of the jinja2 control structure/flow tags. But please
avoid using the following tags since they are not supported: `block`,
`extends`, `macro`, `call`, `include` and `import`.
