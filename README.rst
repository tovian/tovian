======================================
**Tovian** - Tool for video annotation
======================================

Tool for multimodal annotation (audio, video).

*warning:* Documentation update is in progress...

Author: University of West Bohemia, Pilsen, Czech Republic. (Pavel Campr / campr@kky.zcu.cz, Milan Herbig / herbig@students.zcu.cz)


Installation - for annotators
=============================

Windows
-------

Windows binaries can be downloaded from http://tovian.zcu.cz/packages/tovian_win32_stable.zip in a single ZIP file.

Unzip the file in your destination folder. Copy file ``config.ini.dist`` to ``config.ini``. Open ``config.ini`` and edit the configuration values (mainly the database url), which should be given by the administrators. The application is now ready to run.

*warning:* Due to an uknown bug, the destination folder or its parental folders cannot contain special characters and diacritical marks.

Linux
-----

Currently no Linux binaries are provided.


Installation of database - for administrators
=============================================

The application was tested with MySQL and SQLite database engines.

MySQL is expected to be running on a central server. The annotators connect to the same server and share data. Database url in ``config.ini`` has this form:

    database.url:               mysql://database_user:database_password@server/database_name?charset=utf8

Note: Please note ``?charset=utf8`` at the end, which prevents some problems with encoding.

SQLite can be used for local usage without network connection to a central database server. Database url in ``config.ini`` has this form:

   database.url:               sqlite:///data/tovian.db

Note: The path ``data/tovian.db`` is relative. You can specify full path: ``sqlite:////absolute/path/to/tovian.db``


Step 1 - Create new database
----------------------------

To create new database (database name e.g. ``tovian_dopanar``), execute this SQL command in your database engine:

.. code:: sql

    CREATE DATABASE `tovian_dopanar`;

Step 2 - Create database users
------------------------------

One user for administration, one for annotators.

Admin user has full access to all tables. Normal user, used by annotators, has read-only access to all tables and write access to tables ``annotation_values`` and ``annotation_objects``.

Create admin user with full access to the database (user name e.g. ``tov_dopanar_adm``, password ``111``):

.. code:: sql

    USE `tovian_dopanar`;

    CREATE USER 'tov_dopanar_adm'@'%' IDENTIFIED BY '111';
    GRANT ALL PRIVILEGES ON tovian_dopanar.* TO 'tov_dopanar_adm'@'%';
    FLUSH PRIVILEGES;

Create limited user with read-only access to all tables and write access to annotation tables (user name e.g. ``tov_dopanar_user``, password ``222``):

.. code:: sql

    USE `tovian_dopanar`;

    CREATE TABLE `annotation_values` (`foo` int NOT NULL);
    CREATE TABLE `annotation_objects` (`foo` int NOT NULL);
    CREATE TABLE `logs` (`foo` int NOT NULL);

    CREATE USER 'tov_dopanar_user'@'%' IDENTIFIED BY '222';
    GRANT SELECT, SHOW VIEW ON tovian_dopanar.* TO 'tov_dopanar_user'@'%';
    GRANT DELETE, INSERT, REFERENCES, SELECT, SHOW VIEW, UPDATE ON tovian_dopanar.annotation_values TO 'tov_dopanar_user'@'%';
    GRANT DELETE, INSERT, REFERENCES, SELECT, SHOW VIEW, UPDATE ON tovian_dopanar.annotation_objects TO 'tov_dopanar_user'@'%';
    GRANT DELETE, INSERT, REFERENCES, SELECT, SHOW VIEW, UPDATE ON tovian_dopanar.logs TO 'tov_dopanar_user'@'%';
    FLUSH PRIVILEGES;

    DROP TABLE `annotation_objects`, `annotation_values`, `logs`;

Note: Two temporary tables were created do allow granting the priviliges to these tables, which are dropped after. These tables will be created automatically again in the next step.


Step 3 - Set database urls in config.ini
----------------------------------------

Update database urls in file ``config.ini``:

* In section ``[DEFAULT]``, use ``database.url`` with the limited user (as in example above, ``tov_dopanar_user``).
* In section ``[admin]``, use ``database.url`` with the admin user (as in example above, ``tov_dopanar_adm``).


Step 4 - Create tables
----------------------

Tables are automatically created by commandline task:

.. code:: sh

   tovian_cli init_db

Some default data must be loaded into the database:

.. code:: sh

   tovian_cli init_default_data

The database is now fully initialized and ready to use.


Preparation for annotation
=============================================

Before annotation, annotator accounts and information about annotated videos must be added to database.

Create account for new annotator
--------------------------------

Edit directly the ``annotators`` database table, or use interactive commandline task:

.. code:: sh

   tovian_cli add annotator


Add video
---------

Edit directly the ``videos`` table, or use interactive commandline task:

.. code:: sh

   tovian_cli add video


Assign video to annotator
-------------------------

To assign video for annotator, use interactive commandline task:

.. code:: sh

   tovian_cli add video_for_annotator

Now, annotator can execute ``tovian_gui`` and start annotation of assigned videos.
