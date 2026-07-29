import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from instagrapi import Client

from yourapp.models import Post, Interval  # مسیر app خودتون رو بذارید


INTERVAL_FOLDER_NAMES = {
    Interval.BEFORE: "before",
    Interval.CURRENT: "current",
    Interval.AFTER: "after",
}


def download_media(cl: Client, media, folder: str):
    os.makedirs(folder, exist_ok=True)
    try:
        if media.media_type == 1:
            cl.photo_download(media.pk, folder)
        elif media.media_type == 2:
            cl.video_download(media.pk, folder)
        elif media.media_type == 8:
            cl.album_download(media.pk, folder)
        print(f"    ✓ Downloaded {media.pk}")
        return True
    except Exception as e:
        print(f"    [!] Failed to download {media.pk}: {e}")
        return False


class Command(BaseCommand):
    help = "Download media for posts where is_media_saved=False and mark them as saved"

    def add_arguments(self, parser):
        parser.add_argument(
            "--session",
            type=str,
            default=None,
            help="مسیر فایل session ذخیره‌شده‌ی instagrapi (برای لاگین بدون یوزر/پس)",
        )
        parser.add_argument(
            "--username",
            type=str,
            default=None,
            help="یوزرنیم اینستاگرام (در صورت نبود session)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help="پسورد اینستاگرام (در صورت نبود session)",
        )
        parser.add_argument(
            "--base-folder",
            type=str,
            default=None,
            help="پوشه پایه برای دانلود مدیا (پیش‌فرض: MEDIA_ROOT از settings)",
        )
        parser.add_argument(
            "--page",
            type=str,
            default=None,
            help="اگه بدید، فقط پست‌های این پیج (username) دانلود می‌شن",
        )

    def get_client(self, options) -> Client:
        cl = Client()
        session_path = options["session"]
        username = options["username"]
        password = options["password"]

        if session_path and os.path.exists(session_path):
            cl.load_settings(session_path)
            if username and password:
                # این حالت وقتیه که session قدیمی شده و می‌خوایم دوباره لاگین کنیم
                cl.login(username, password)
        elif username and password:
            cl.login(username, password)
            if session_path:
                cl.dump_settings(session_path)
        else:
            raise CommandError(
                "برای اتصال به اینستاگرام باید --session یا --username و --password بدید"
            )

        return cl

    def handle(self, *args, **options):
        cl = self.get_client(options)

        base_folder = options["base_folder"] or str(getattr(settings, "MEDIA_ROOT", "media"))

        posts_qs = Post.objects.filter(is_media_saved=False).select_related("page")
        if options["page"]:
            posts_qs = posts_qs.filter(page__username=options["page"])

        total = posts_qs.count()
        if total == 0:
            self.stdout.write("post with is_media_saved=False not found.")
            return

        self.stdout.write(f" {total} posts found to download.\n")

        success_count = 0
        fail_count = 0

        for post in posts_qs:
            interval_folder = INTERVAL_FOLDER_NAMES.get(post.interval, "unknown")
            post_folder = os.path.join(
                base_folder, post.page.username, interval_folder, post.short_code
            )
            os.makedirs(post_folder, exist_ok=True)

            self.stdout.write(f"loading... {post.short_code} ...")

            try:
                media = cl.media_info(int(post.original_pk))
            except Exception as e:
                self.stderr.write(
                    self.style.WARNING(
                        f"    [!] getting information for {post.short_code} failed: {e}"
                    )
                )
                fail_count += 1
                continue

            ok = download_media(cl, media, post_folder)

            if ok:
                caption_path = os.path.join(post_folder, "caption.txt")
                with open(caption_path, "w", encoding="utf-8") as f:
                    f.write(post.caption or "")

                post.is_media_saved = True
                post.save(update_fields=["is_media_saved"])
                success_count += 1
            else:
                fail_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nfinished. success: {success_count} | failed: {fail_count}"
            )
        )