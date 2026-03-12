from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY


class Database:
    def __init__(self):
        self._client: Client | None = None

    @property
    def client(self) -> Client | None:
        if not self._client and SUPABASE_URL and SUPABASE_KEY:
            self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return self._client

    def is_connected(self) -> bool:
        return self.client is not None

    def create_test_run(self, browser: str, platform: str, session_id: str = "") -> dict:
        if not self.is_connected():
            return {}
        try:
            result = self.client.table("test_runs").insert({
                "browser":                 browser,
                "platform":                platform,
                "status":                  "running",
                "browserstack_session_id": session_id,
            }).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"[DB] create_test_run error: {e}")
            return {}

    def update_test_run_status(self, run_id: str, status: str):
        if not self.is_connected():
            return
        try:
            self.client.table("test_runs").update(
                {"status": status}
            ).eq("id", run_id).execute()
        except Exception as e:
            print(f"[DB] update_test_run_status error: {e}")

    def get_all_test_runs(self) -> list:
        if not self.is_connected():
            return []
        try:
            result = (
                self.client.table("test_runs")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[DB] get_all_test_runs error: {e}")
            return []

    def save_article(self, article: dict) -> dict:
        if not self.is_connected():
            return {}
        try:
            result = self.client.table("articles").insert({
                "test_run_id":      article.get("test_run_id"),
                "title_es":         article.get("title", ""),
                "title_en":         article.get("title_en", ""),
                "content_es":       article.get("content", ""),
                "content_en":       article.get("content_en", ""),
                "image_url":        article.get("image_url", ""),
                "image_local_path": article.get("image_local_path", ""),
                "article_url":      article.get("article_url", ""),
            }).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"[DB] save_article error: {e}")
            return {}

    def update_article_translation(self, article_id: str, title_en: str):
        if not self.is_connected():
            return
        try:
            self.client.table("articles").update(
                {"title_en": title_en}
            ).eq("id", article_id).execute()
        except Exception as e:
            print(f"[DB] update_article_translation error: {e}")

    def update_article_content_translation(self, article_id: str, content_en: str):
        if not self.is_connected():
            return
        try:
            self.client.table("articles").update(
                {"content_en": content_en}
            ).eq("id", article_id).execute()
        except Exception as e:
            print(f"[DB] update_article_content_translation error: {e}")

    def get_all_articles(self) -> list:
        if not self.is_connected():
            return []
        try:
            result = (
                self.client.table("articles")
                .select("*")
                .order("scraped_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[DB] get_all_articles error: {e}")
            return []

    def get_articles_by_run(self, run_id: str) -> list:
        if not self.is_connected():
            return []
        try:
            result = (
                self.client.table("articles")
                .select("*")
                .eq("test_run_id", run_id)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[DB] get_articles_by_run error: {e}")
            return {}

    def save_word_frequency(self, run_id: str, word_freq: dict):
        if not self.is_connected():
            return
        try:
            rows = [
                {"test_run_id": run_id, "word": word, "count": count}
                for word, count in word_freq.items()
            ]
            if rows:
                self.client.table("word_frequency").insert(rows).execute()
        except Exception as e:
            print(f"[DB] save_word_frequency error: {e}")

    def get_word_frequency_by_run(self, run_id: str) -> list:
        if not self.is_connected():
            return []
        try:
            result = (
                self.client.table("word_frequency")
                .select("*")
                .eq("test_run_id", run_id)
                .order("count", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[DB] get_word_frequency_by_run error: {e}")
            return []


db = Database()