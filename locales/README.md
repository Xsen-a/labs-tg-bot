***Компиляция файла локализации***
```
msgfmt messages.po -o messages.mo
```

***Создать папку локалей для конкретного языка***
```commandline
pybabel init -i locales/messages.pot -d locales -D messages -l ru
```
***Создать .pot файл***
```commandline
pybabel extract -F babel.cfg -o locales/messages.pot .
```
***Обновить .po файлы***
```commandline
pybabel update -d locales -D messages -i locales/messages.pot
```
***Компиляция .mo файла***
```commandline
pybabel compile -d locales -D messages
```