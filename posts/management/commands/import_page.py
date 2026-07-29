import json

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from posts.models import Page, Post, Interval


class Command(BaseCommand):
    help = "Import posts from a JSON export file into the database"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="مسیر فایل JSON")

    def handle(self, *args, **options):
        file_path = options["json_file"]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"فایل پیدا نشد: {file_path}")
        except json.JSONDecodeError as e:
            raise CommandError(f"فایل JSON معتبر نیست: {e}")

        page_name = data.get("page_name")
        if not page_name:
            raise CommandError("page_name field not found")

        page, created = Page.objects.get_or_create(username=page_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f"page created: {page_name}"))
        else:
            self.stdout.write(f"page already exists: {page_name}")
        # s = data['counts']['before'] + data['counts']['current'] + data['counts']['after']
        # print('supposed to be:', s)
        interval_map = {
            "before_posts": Interval.BEFORE,
            "current_posts": Interval.CURRENT,
            "after_posts": Interval.AFTER,
        }

        created_count = 0
        updated_count = 0
        skipped_count = 0
        tmp = 1
        for key, interval_value in interval_map.items():
            posts_list = data.get(key, [])

            for post_data in posts_list:
                try:
                    original_pk = str(post_data.get("post_pk", tmp))
                    tmp += 1
                    short_code = post_data["post_url"]
                    taken_at_raw = post_data["taken_at"]
                except KeyError as e:
                    self.stderr.write(
                        self.style.WARNING(f"فیلد {e} وجود نداشت، این آیتم رد شد: {post_data}")
                    )
                    skipped_count += 1
                    continue

                caption = post_data.get("caption", "")

                taken_at = parse_datetime(taken_at_raw)
                if taken_at is None:
                    self.stderr.write(
                        self.style.WARNING(f"تاریخ نامعتبر: {taken_at_raw} - رد شد, {post_data}")
                    )
                    skipped_count += 1
                    continue

                # اگه USE_TZ=True باشه و رشته‌ی تاریخ timezone نداشته باشه، باید aware بشه
                if timezone.is_naive(taken_at) and getattr(timezone, "get_current_timezone", None):
                    try:
                        taken_at = timezone.make_aware(taken_at)
                    except ValueError:
                        pass  # از قبل aware بوده

                post, was_created = Post.objects.update_or_create(
                    page=page,
                    original_pk=original_pk,
                    defaults={
                        "short_code": short_code,
                        "taken_at": taken_at,
                        "caption": caption,
                        "interval": interval_value,
                    },
                )

                if was_created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"finished. created: {created_count} | updated: {updated_count} | rejected: {skipped_count}"
            )
        )
