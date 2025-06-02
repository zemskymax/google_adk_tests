import asyncpraw
from .env_variable_handler import EnvironmentVariableHandler


TEXT_TO_EXCLUDE = "I am a bot, and this action was performed automatically."

class RedditAPIHandler:
    """Handles Reddit API interactions."""
    def __init__(self) -> None:
        self.rd = None
        self._validate_environment_variables()
        self._init_reddit()

    def _validate_environment_variables(self):
        env_manager = EnvironmentVariableHandler()

        self.reddit_client_id = env_manager.get_value_from_env_variable("REDDIT_CLIENT_ID")
        self.reddit_client_secret = env_manager.get_value_from_env_variable("REDDIT_CLIENT_SECRET")
        print(f"Reddit Client ID: {self.reddit_client_id} - Reddit Client SECRET: {self.reddit_client_secret}")

    def _init_reddit(self):
        if not (self.reddit_client_id and self.reddit_client_secret):
            print("Cannot initialize PRAW: Reddit Client ID or Secret is missing.")
            return
        try:
            self.rd = asyncpraw.Reddit(client_id=self.reddit_client_id,
                                  client_secret=self.reddit_client_secret,
                                  user_agent="gemini_adk_reddit_agent/v1.0")
            print("PRAW initialized successfully.")

            # print(f"PRAW initialized. Hot posts in r/python: {[p.title for p in self.rd.subreddit('python').hot(limit=1)]}")
        except Exception as e:
            print(f"Error initializing PRAW: {e}")
            self.rd = None

    async def get_post_content(self, url_or_id: str) -> dict:
        """Fetch specific reddit post (with comments) using Reddit API."""
        print("Fetching post content...")
        if not self.rd:
            return {"error": "PRAW Reddit instance not initialized."}
        try:
            if "reddit.com" in url_or_id:
                submission = await self.rd.submission(url=url_or_id)
            else:
                submission = await self.rd.submission(id=url_or_id)
        except Exception as e:
            print(f"Error fetching submission '{url_or_id}': {e}")
            return {"error": f"Could not fetch Reddit submission: {e}"}

        reddit_post = {}
        reddit_post["title"] = submission.title
        reddit_post["body"] = submission.selftext
        reddit_post["score"] = submission.score
        reddit_post["author"] = str(submission.author.name) if submission.author else "Unknown"
        print(f"Post title: {submission.title} - Post author: {reddit_post['author']} - Post score: {submission.score}")

        reddit_post["comments"] = []
        await submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            author_name = str(comment.author.name) if comment.author else "[Deleted]"
            author_name = author_name.lower()

            if comment.score <= 0:
                continue
            if "deleted" in comment.body.lower() or "removed" in comment.body.lower():
                continue
            if TEXT_TO_EXCLUDE in comment.body:
                continue
            if "bot" in author_name or "automoderator" in author_name:
                continue
            reddit_post["comments"].append({
                "body": comment.body,
                "score": comment.score,
                "author": author_name
            })

        print("Reddit Post: ", reddit_post)
        return reddit_post
