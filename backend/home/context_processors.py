from home.models import BlogIndexPage, BlogPostPage


def editorial_navigation(request):
    """Expose the journal link only when the maker has published a real post."""
    journal_index = BlogIndexPage.objects.live().first()
    if journal_index and not BlogPostPage.objects.child_of(journal_index).live().exists():
        journal_index = None
    return {"journal_index": journal_index}
