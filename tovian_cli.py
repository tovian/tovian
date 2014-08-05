#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command line interface
"""

__version__ = "$Id: tovian_cli.py 352 2014-03-03 18:22:45Z campr $"

import os
import sys
import logging
import argparse
import datetime
import json
import platform
from collections import defaultdict

import tovian_gui
import tovian.version
from tovian import log


logger = logging.getLogger(__name__)


def action_check(args, root_dir):
    tovian_gui.check_requirements()
    print 'all requirements OK'

def action_video_info(args, root_dir):
    import tovian.video_info

    print tovian.video_info.video_info(args.file)

def action_init_db(args, root_dir):
    models.database.db.recreate_tables()

def action_init_default_data(args, root_dir):
    models.database.db.insert_default_data()

def action_load_fixtures(args, root_dir):
    from tovian.models.tests import fixtures

    models.database.db.session.add_all(fixtures.create_fixtures())
    models.database.db.session.commit()

def action_db_benchmark(args, root_dir):
    ao_football_rectangle_1 = models.repository.annotation_objects.get_one_by_id(1)
    assert ao_football_rectangle_1 is not None

    import time

    n = 100
    durations = []

    for i in range(0, n):
        t1 = time.time()
        ao_football_rectangle_1.annotation_values_local_interpolate_in_frame(8)
        t2 = time.time()
        durations.append(t2 - t1)
        print '%s\r' % (20 * (i + 1) / n * '.'),

    print
    print 'Measurements: %d' % (n)
    print 'Average: %f ms' % (1000 * sum(durations) / n)
    print 'Min: %f ms' % (1000 * min(durations))
    print 'Max: %f ms' % (1000 * max(durations))

def action_export(args, root_dir):
    tables = all_exportable_entities if 'all' in args.tables else args.tables
    data = {}

    # prepare list of videos, if args.videos is given
    video_ids = []

    if args.video is not None:
        for video_id in args.video:
            video = models.repository.videos.get_one(video_id)

            if not video:
                raise Exception('Cannot find video: %s' % (video_id))

            video_ids.append(video.id)

    # export data to dict
    for entity_name in tables:
        entity = getattr(models.entity, entity_name)
        query = models.database.db.session.query(entity)

        if len(video_ids):
            # add special filters to export only data related to given video(s)
            if entity_name=='Video':
                query = query.filter(models.entity.Video.id.in_(video_ids))
            elif entity_name=='Annotator':
                query = query.join(models.entity.Video.annotators)
                query = query.filter(models.entity.Video.id.in_(video_ids))
            elif entity_name=='AnnotationAttribute':
                query = query.join(models.entity.Video.annotation_attributes)
                query = query.filter(models.entity.Video.id.in_(video_ids))
            elif entity_name=='AnnotationObject':
                query = query.join(models.entity.Video.annotation_objects)
                query = query.filter(models.entity.Video.id.in_(video_ids))
            elif entity_name=='AnnotationValue':
                query = query.join(models.entity.AnnotationObject)
                query = query.filter(models.entity.AnnotationObject.video_id.in_(video_ids))
            else:
                raise Exception("Video filter is not supported for table '%s'" % (entity_name))

        if args.filter:
            query = query.filter(args.filter)

        items = query.order_by(entity.id).all()

        # interpolate annotation values
        if args.interpolated and entity_name=='AnnotationValue':
            # avs structure:
            #   avs[annotation_object_id][annotation_attribute_id][frame_from] = av
            avs = defaultdict(lambda: defaultdict(dict))

            # fill in avs
            for av in items:
                frame_from = av.frame_from

                # ignore global annotation values (they are not interpolated)
                if frame_from is None:
                    continue

                annotation_object_id = av.annotation_object_id
                annotation_attribute_id = av.annotation_attribute_id

                avs[annotation_object_id][annotation_attribute_id][frame_from] = av

            # loop in avs, interpolated values are appended to items
            for annotation_object_id, avs_of_object in avs.iteritems():
                for annotation_attribute_id, avs_of_attribute in avs_of_object.iteritems():
                    frames = sorted(avs_of_attribute.keys())

                    for offset in range(1, len(frames)):
                        frame_left = frames[offset-1]
                        frame_right = frames[offset]

                        av_left = avs_of_attribute[frame_left]
                        av_right = avs_of_attribute[frame_right]

                        for frame in range(frame_left+1, frame_right):
                            av_interpolated = models.entity.AnnotationValue.interpolate(av_left, av_right, frame)

                            if av_interpolated.annotation_attribute_id is None:
                                raise Exception('annotation_attribute_id cannot be None')

                            items.append(av_interpolated)

        data[entity_name] = []

        for item in items:
            # export attributes
            # ignore object attributes starting with "_", convert long to int
            d = {}

            for k in item.__dict__.keys():
                v = item.__dict__[k]

                if k.startswith('_'):
                    # try if it is not a synonym (i.e. has same attribute without "_")
                    try:
                        k2 = k[1:]
                        d[k2] = getattr(item, k2)
                    except:
                        pass

                    continue

                # convert long to int
                if type(v) is long:
                    v = int(v)

                # ignore e.g. "annotation_object" when "annotation_object_id" exists
                if (k + '_id') in item.__dict__:
                    continue

                d[k] = v

            # export relations
            for relation in item.__mapper__.relationships:
                if relation.direction.name in ['ONETOMANY', 'MANYTOMANY']:
                    # show primary keys, convert long to int
                    d[relation.key] = [int(o.id) for o in getattr(item, relation.key)]

            data[entity_name].append(d)

    # write output
    if args.format == 'json':
        # datetime objects cannot be serialized by default
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        print json.dumps(data, default=dthandler)

    elif args.format == 'yaml':
        import yaml

        print yaml.safe_dump(data, allow_unicode=True, indent=4, width=1000)

    elif args.format == 'csv':
        import csv

        for table_name, table_data in data.iteritems():
            keys = sorted(table_data[0].keys())
            dict_writer = csv.DictWriter(sys.stdout, keys)

            dict_writer.writer.writerow([table_name])
            dict_writer.writer.writerow(keys)
            dict_writer.writerows(table_data)
            dict_writer.writer.writerow([])

    elif args.format == 'print':
        import pprint

        pprint.pprint(data)

    else:
        raise Exception('Unsupported export format: %s' % (args.format))

def action_import(args, root_dir):
    if args.type == 'annotations':
        pass
    else:
        raise Exception('Unsupported type for import: %s' % (args.type))

    # load data
    if args.format == 'json':
        with open(args.file) as fr:
            data = json.load(fr)
    elif args.format == 'yaml':
        import yaml

        with open(args.file) as fr:
            print yaml.load(fr)
    else:
        raise Exception('Unsupported format for import: %s' % (args.format))

    if args.annotator is not None:
        annotator = models.repository.annotators.get_one(args.annotator)

        if annotator is None:
            raise Exception('Cannot find annotator by id, name or email: %s' % (args.annotator))
    else:
        annotator = None

    for video_id, aos_data in data.iteritems():
        logger.info("Importing for video: %s" % (video_id))

        # name can be video's name or filename, try to select by both
        video = models.repository.videos.get_one(video_id)

        if video is None:
            raise Exception('Video with name or filename not found: %s' % (video_id))

        video.import_annotations(aos_data, annotator=annotator)

        logger.info("Data loaded, committing to database.")

        models.database.db.session.commit()

def print_available_annotation_attributes():
    aas = models.repository.annotation_attributes.get_all()

    print 'Available annotation attributes:'
    print '----- -----------------------------------'
    print '%-5s %s' % ('ID', 'name')
    print '----- -----------------------------------'

    for aa in aas:
        print '%-5d %s' % (aa.id, aa.name.encode('utf8'))

    print '----- -----------------------------------'

def print_available_annotators():
    annotators = models.repository.annotators.get_all()

    print 'Available annotators:'
    print '----- ------------------------- --------------------'
    print '%-5s %-25s %s' % ('ID', 'email', 'name')
    print '----- ------------------------- --------------------'

    for annotator in annotators:
        print '%-5d %-25s %s' % (annotator.id, annotator.email.encode('utf8'), annotator.name.encode('utf8'))

    print '----- ------------------------- --------------------'

def print_available_videos():
    videos = models.repository.videos.get_all()

    print 'Available videos:'
    print '----- ----------------------------------- -------------------------'
    print '%-5s %-35s %s' % ('ID', 'filename', 'name')
    print '----- ----------------------------------- -------------------------'

    for video in videos:
        print '%-5d %-35s %s' % (video.id, video.filename.encode('utf8'), video.name.encode('utf8'))

    print '----- ----------------------------------- -------------------------'

def action_add(args, root_dir):
    import tovian.cli.interactive as interactive
    import tovian.video_info

    if args.type == 'annotator':
        print interactive.format_header('Add new annotator:')

        annotator = models.entity.Annotator()
        annotator.name = interactive.input("Annotator name:")
        annotator.email = interactive.input("Annotator email:")
        annotator.password = interactive.input_password("Annotator password:")
        annotator.phone = interactive.input("Annotator phone (can be empty):", allow_empty=True)
        annotator.internal_comment = interactive.input("Annotator internal comment (can be empty):", allow_empty=True)
        annotator.is_enabled = interactive.input("Annotator is enabled (0 / 1):", type='bool')

        # master_id
        print interactive.format_prompt("Annotator's master (supervisor):")
        master = None

        print_available_annotators()

        while True:
            master_id = interactive.input(interactive.format_prompt("  [id, name or email] (can be empty):"), allow_empty=True)

            if master_id is None:
                break

            master = models.repository.annotators.get_one(master_id)

            if master is None:
                print interactive.format_error('  Cannot find annotator "%s"!' % (master_id))
            else:
                break

        if master is not None:
            annotator.master_id = master.id

        models.database.db.session.add(annotator)
        models.database.db.session.commit()

        print "Annotator was created, ID = %d" % (annotator.id)

    elif args.type == 'video':
        print interactive.format_header('Add new video:')

        video = models.entity.Video()
        video.name = interactive.input("Video name:")
        video.filename = interactive.input("Video filename:")
        video.url_download = interactive.input("Video download URL:")
        video.public_comment = interactive.input("Video public comment (can be empty):", allow_empty=True)

        print 'Trying to get information about video file...',

        video_info = tovian.video_info.video_info(os.path.join(root_dir, 'data', 'video', video.filename))

        if len(video_info) == 0:
            print 'Failed from local file, trying from download URL...',

            video_info = tovian.video_info.video_info(video.url_download)

        if len(video_info):
            print 'OK!', video_info
        else:
            print 'No information available. Is video URL correct? Do you have "ffprobe" in your path?'

        video.fps = interactive.input("Video FPS:", type='float', default_value=video_info['fps'] if 'fps' in video_info else None)
        video.frame_count = interactive.input("Video frame count:", type='int', default_value=video_info['frames'] if 'frames' in video_info else None)
        video.duration = interactive.input("Video duration (s):", type='float', default_value=video_info['duration'] if 'duration' in video_info else None)
        video.width = interactive.input("Video width:", type='int', default_value=video_info['width'] if 'width' in video_info else None)
        video.height = interactive.input("Video height:", type='int', default_value=video_info['height'] if 'height' in video_info else None)
        video.is_enabled = interactive.input("Video is enabled (0 / 1):", type='bool')
        video.is_finished = interactive.input("Video is finished (0 / 1):", type='bool')
        video.allowed_annotation_object_types = interactive.input("Video allowed annotation object types (e.g. 'rectangle circle point nonvisual'):")

        # uploader_id
        print interactive.format_prompt("Video uploader (annotator):")

        print_available_annotators()

        while True:
            uploader_id = interactive.input("  [id, name or email]:")

            if uploader_id is None:
                break

            uploader = models.repository.annotators.get_one(uploader_id)

            if uploader is None:
                print interactive.format_error('  Cannot find annotator "%s"!' % (uploader_id))
            else:
                break

        video.uploader_id = uploader.id

        # annotation_attributes
        print interactive.format_prompt('Add multiple annotation attributes:')

        annotation_attributes = []

        print_available_annotation_attributes()

        while True:
            annotation_attribute_id = interactive.input("  Add annotation attribute [id or name] (enter nothing to stop adding):", allow_empty=True)

            if annotation_attribute_id is None:
                break

            annotation_attribute = models.repository.annotation_attributes.get_one(annotation_attribute_id)

            if annotation_attribute is None:
                print interactive.format_error('  Cannot find annotation attribute "%s"!' % (annotation_attribute_id))
            else:
                annotation_attributes.append(annotation_attribute)

        video.annotation_attributes = annotation_attributes

        models.database.db.session.add(video)
        models.database.db.session.commit()

        print "Video was created, ID = %d" % (video.id)

    elif args.type == 'video_for_annotator':
        print interactive.format_header('Assign video(s) to annotator(s):')

        # annotators
        print interactive.format_prompt('Select one or more annotators:')
        annotators = []

        print_available_annotators()

        while True:
            annotator_id = interactive.input("  Add annotator [id, name or email] (enter nothing to stop):", allow_empty=True)

            if annotator_id is None:
                break

            annotator = models.repository.annotators.get_one(annotator_id)

            if annotator is None:
                print interactive.format_error('  Cannot find annotator "%s"!' % (annotator_id))
            else:
                annotators.append(annotator)

        # videos
        print interactive.format_prompt('Select one or more videos, which will be assigned to previously selected annotator(s):')
        videos = []

        print_available_videos()

        while True:
            video_id = interactive.input("  Add video [id, name or filename] (enter nothing to stop):", allow_empty=True)

            if video_id is None:
                break

            video = models.repository.videos.get_one(video_id)

            if video is None:
                print interactive.format_error('  Cannot find video "%s"!' % (video_id))
            else:
                videos.append(video)

        # assign annotators and videos
        for video in videos:
            video.annotators += annotators

        models.database.db.session.commit()

    else:
        raise Exception('Unsupported type for add: %s' % (args.type))

def action_update(args, root_dir):
    import urllib2
    import zipfile
    import shutil

    if not sys.argv[0].endswith('.exe'):
        raise Exception('Update can be used only for Windows binary distribution')

    # download package (zip file)
    packages_url = config.config.get(args.environment, 'packages.url').strip('/')

    fn = 'tovian_' + args.revision + '.zip'
    download_from = packages_url + '/' + fn
    download_to = os.path.join(root_dir, fn)

    try:
        r = urllib2.urlopen(download_from)

        with open(download_to, 'wb') as fr:
            fr.write(r.read())
    except Exception as e:
        raise Exception("Download from %s failed (%s). Either the package url is wrong (%s) or revision doesn't exist (%s)." % (download_from, e.msg, packages_url, args.revision))

    # extract package to data/update
    update_dir = os.path.join(root_dir, 'data', 'update')

    if os.path.isdir(update_dir):
        # remove previous update directory
        shutil.rmtree(update_dir)

    os.mkdir(update_dir)

    with zipfile.ZipFile(download_to, 'r') as zip_file:
        for fn in zip_file.namelist():
            logger.debug("Extracting %s" % (fn))
            zip_file.extract(fn, update_dir)

    os.remove(download_to)

    logger.info("Update is ready in direcory:\n%s\nPlease move the files to the application directory to finish the update." % (update_dir))


if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.realpath(sys.argv[0]))

    all_exportable_entities = ['Annotator', 'Video', 'AnnotationAttribute', 'AnnotationObject', 'AnnotationValue']
    actions_using_database = ['init_db', 'load_fixtures', 'db_benchmark', 'export', 'import', 'add', 'init_default_data']

    version_data, version_info = tovian.version.version(root_dir)

    # parse commandline arguments
    parser = argparse.ArgumentParser(description="Tovian command-line interface" + version_info)
    subparsers = parser.add_subparsers(title="action", dest='action')

    parser_check = subparsers.add_parser('check', help="Check requirements")
    parser_check.add_argument('-e', '--environment', type=str, default='production')

    parser_video_info = subparsers.add_parser('video_info', help="Print information about a video file (or URL)")
    parser_video_info.add_argument('-e', '--environment', type=str, default='production')
    parser_video_info.add_argument('file')

    parser_init_db = subparsers.add_parser('init_db', help="Initialize database structure (drops existing tables!)")
    parser_init_db.add_argument('-e', '--environment', type=str, default='admin')

    parser_init_default_data = subparsers.add_parser('init_default_data', help="Initialize default database data")
    parser_init_default_data.add_argument('-e', '--environment', type=str, default='admin')

    parser_load_fixtures = subparsers.add_parser('load_fixtures', help="Load testing data")
    parser_load_fixtures.add_argument('-e', '--environment', type=str, default='admin')

    parser_db_benchmark = subparsers.add_parser('db_benchmark', help="Benchmark database speed")
    parser_db_benchmark.add_argument('-e', '--environment', type=str, default='production')

    parser_export = subparsers.add_parser('export', help="Export data to console. Redirect output to file by adding e.g. '> file.json' to command")
    parser_export.add_argument('tables', choices=all_exportable_entities + ['all'], nargs='+')
    parser_export.add_argument('-e', '--environment', type=str, default='production')
    parser_export.add_argument('-f', '--format', choices=['json', 'yaml', 'csv', 'print'], default='json')
    parser_export.add_argument('--filter', help="Custom filter, e.g. 'id>10'")
    parser_export.add_argument('--video', help="Only items related to given video(s) will be exported. Video IDs, names or filenames are accepted.", nargs='+')
    parser_export.add_argument('-i', '--interpolated', action='store_true', help='export with interpolated annotation values')

    parser_import = subparsers.add_parser('import', help="Import data")
    parser_import.add_argument('type', choices=['annotations'])
    parser_import.add_argument('file')
    parser_import.add_argument('-e', '--environment', type=str, default='production')
    parser_import.add_argument('-a', '--annotator', help="Annotator (id, name or email) from database, who will be connected to imported data")
    parser_import.add_argument('-f', '--format', choices=['json', 'yaml'], default='json')

    parser_add = subparsers.add_parser('add', help="Add data interactively")
    parser_add.add_argument('type', choices=['annotator', 'video', 'video_for_annotator'])
    parser_add.add_argument('-e', '--environment', type=str, default='admin')

    parser_update = subparsers.add_parser('update', help="Update Tovian program. Only for Windows builds.")
    parser_update.add_argument('revision', default=['win32_stable'])
    parser_update.add_argument('-e', '--environment', type=str, default='production')

    args = parser.parse_args()


    # initialize logging before anything else
    log_dir = os.path.join(root_dir, 'log')

    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    log.setup_logging(os.path.join(root_dir, 'data', tovian_gui.environments[args.environment]['logging_config_file']), log_dir=log_dir)

    # import after logging is initialized
    from tovian import config

    # load configuration
    config.load(os.path.join(root_dir, 'config.ini'))

    # start
    logger.debug("Start CLI, environment = %s" % (args.environment))

    if args.action in actions_using_database:
        from tovian import models
        # initialize database connection
        models.database.db.open_from_config(config.config, args.environment)

    # process actions
    try:
        action_function = locals()['action_' + args.action]
    except KeyError as e:
        raise Exception("Unsupported action: %s" % (args.action))

    if args.action in actions_using_database and args.action not in ['init_db']:
        # logging
        models.repository.logs.insert('cli.start', {
            'args': vars(args),
            'root_dir': root_dir,
            'platform': {'platform': platform.platform(), 'uname': platform.uname()},
            'tovian': version_data
        })

    # execute action
    action_function(args, root_dir)

    if args.action in actions_using_database:
        models.repository.logs.insert('cli.stop', {'db_sql_count': models.database.db.profiler['sql_count']})
