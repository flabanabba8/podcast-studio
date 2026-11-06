import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('podcast', Path(__file__).resolve().parents[1] / '__init__.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)

class PodcastTest(unittest.TestCase):
 def test_review_detects_any_script_or_source_change(self):
  segments = [{'title': 'A discovery', 'sources': ['Primary paper'], 'turns': [{'speaker': 'A', 'text': 'Here is the finding.'}]}]
  digest = p.check_script(segments)['segments'][0]['sha256']
  review = {'reviewer': 'editor', 'segments': [{'sha256': digest, 'purpose': 'Explain finding', 'opening_check': 'Names the result', 'source_check': 'Compared with paper', 'edits': 'Clarified the setup'}]}
  self.assertEqual(p.check_review(segments, review)['status'], 'review_record_matches_script')
  self.assertEqual(p.pagecast_plan(segments, review)['assignments'], [{'paragraph': 0, 'speaker': 'A'}])
  segments[0]['turns'][0]['text'] += ' Changed.'
  with self.assertRaisesRegex(ValueError, 'changed'): p.check_review(segments, review)
  with self.assertRaisesRegex(ValueError, 'changed'): p.pagecast_plan(segments, review)
  segments[0]['turns'][0]['text'] = 'Here is the finding.'
  segments[0]['sources'][0] = 'Different source'
  with self.assertRaisesRegex(ValueError, 'changed'): p.check_review(segments, review)
 def test_missing_sources_and_incomplete_review_fail(self):
  segments = [{'title': 'A', 'sources': [], 'turns': [{'speaker': 'A', 'text': 'Hello.'}]}]
  with self.assertRaises(ValueError): p.check_script(segments)
  segments[0]['sources'] = ['Paper']
  with self.assertRaises(ValueError): p.check_review(segments, {'reviewer': 'editor', 'segments': []})

 def test_registered_skill_and_handler(self):
  class Context:
   def __init__(self): self.skills = []; self.tools = {}
   def register_skill(self, name, path, **kwargs): self.skills.append((name, path))
   def register_tool(self, **kwargs): self.tools[kwargs['name']] = kwargs
  ctx = Context(); p.register(ctx)
  self.assertEqual(len(ctx.skills), 1)
  self.assertTrue(ctx.skills[0][1].is_file())
  result = json.loads(ctx.tools['podcast_check_script']['handler']({'segments': [{'title': 'Test', 'sources': ['Paper'], 'turns': [{'speaker': 'Host', 'text': 'A finding.'}]}]}))
  self.assertNotIn('error', result)

if __name__ == '__main__': unittest.main()
