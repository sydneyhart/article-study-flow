import http.client
import json
import threading
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import app
from core import *

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.csv = (Path(__file__).parents[1] / 'data/readings.csv').read_text()
        self.rows = read_csv(self.csv)

    def test_fixture_batch_and_exports(self):
        results = process(self.rows, demo=True)
        self.assertEqual(len(results), 4)
        self.assertTrue(all(r['status'] == 'ok' for r in results))
        for result in results:
            self.assertEqual(set(result['summary']), set(FIELDS))
        self.assertIn('## Practice quizzes', export(results))
        self.assertIn('<h3>Evidence</h3>', export(results, 'html'))

    def test_csv_quoted_bom_duplicates_blank(self):
        rows = read_csv('\ufeffurl,title,text\nhttps://example.org,"Title, quoted","a,b"\nhttps://example.org,duplicate,\n,,\n')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['title'], 'Title, quoted')

    def test_bad_csv_and_row_limit(self):
        for value in ['title\nMissing URL', 'url\n', 'url\n'+'\n'.join('https://example.org/'+str(i) for i in range(26))]:
            with self.assertRaises(ValueError): read_csv(value)

    def test_sensitive_never_fetched(self):
        row = dict(self.rows[0], text='', sensitive='yes')
        with patch('core.fetch_article') as fetch:
            result = process([row], fetch=True)
            fetch.assert_not_called()
            self.assertEqual(result[0]['status'], 'error')

    def test_fetch_requires_opt_in(self):
        with patch('core.fetch_article') as fetch:
            result = process([dict(self.rows[0], text='')])
            fetch.assert_not_called()
            self.assertEqual(result[0]['status'], 'error')

    def test_public_network_restrictions(self):
        for url in ['file:///etc/passwd', 'http://example.org', 'https://user:password@example.org', 'https://example.org:444']:
            with self.assertRaises(ValueError): fetch_article(url)
        for ip in ['127.0.0.1', '10.1.2.3', '169.254.169.254', '::1']:
            with patch('core.socket.getaddrinfo', return_value=[(2,1,6,'',(ip,443))]):
                with self.assertRaises(ValueError): fetch_article('https://example.org')

    def test_redirect_revalidates_destination(self):
        connection = MagicMock()
        response = connection.getresponse.return_value
        response.status = 302
        response.getheader.return_value = 'http://127.0.0.1/secret'
        with patch('core.socket.getaddrinfo', return_value=[(2,1,6,'',('93.184.216.34',443))]), patch('core.http.client.HTTPSConnection', return_value=connection):
            with self.assertRaises(ValueError): fetch_article('https://example.org')

    def test_unverified_evidence_and_bad_shape(self):
        text = self.rows[0]['text']; good = demo_summary(text)
        for bad in [dict(good, evidence=['Made-up finding']), dict(good, takeaways=[]), dict(good, main_idea=['word '*56]), {'evidence': ['a']}]:
            with self.assertRaises(ValueError): validate_summary(bad, text)

    def test_local_ai_contract(self):
        expected = demo_summary(self.rows[0]['text'])
        connection = MagicMock()
        response = connection.getresponse.return_value
        response.status = 200
        response.read.return_value = json.dumps({'message': {'content': json.dumps(expected)}}).encode()
        with patch('core.http.client.HTTPConnection', return_value=connection) as client:
            self.assertEqual(summarize(self.rows[0]['text'], 'test-local'), expected)
            self.assertEqual(client.call_args.args[:2], ('127.0.0.1', 11434))
            payload = json.loads(connection.request.call_args.args[2])
            self.assertFalse(payload['stream'])
            self.assertEqual(payload['format'], SCHEMA)

    def test_failure_isolation(self):
        rows = [dict(self.rows[0], text=''), self.rows[1]]
        results = process(rows, demo=True)
        self.assertEqual([r['status'] for r in results], ['error', 'ok'])

    def test_ai_short_long_and_invalid_json(self):
        for text in ['short', 'word ' * 9000]:
            with self.assertRaises(ValueError): summarize(text, 'test')
        connection = MagicMock(); connection.getresponse.return_value.status = 200
        connection.getresponse.return_value.read.return_value = b'not json'
        with patch('core.http.client.HTTPConnection', return_value=connection):
            self.assertEqual(process(self.rows[:1])[0]['status'], 'error')

    def test_export_escapes_active_content(self):
        results = process(self.rows[:1], demo=True)
        results[0]['title'] = '<script>alert(1)</script>'
        output = export(results, 'html')
        self.assertNotIn('<script>', output)
        self.assertIn('&lt;script&gt;', output)

    def test_html_parser_removes_scripts(self):
        parser = ArticleParser(); parser.feed('<p>Visible</p><script>secret()</script><p>End</p>')
        self.assertNotIn('secret', ''.join(parser.parts))

    def test_http_end_to_end(self):
        server = app.HTTPServer(('127.0.0.1', 0), app.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
            headers = {'Host': '127.0.0.1:8765', 'Origin': 'http://127.0.0.1:8765', 'Content-Type':'application/json'}
            conn.request('POST', '/summarize', json.dumps({'csv': self.csv, 'demo': True}), headers)
            response = conn.getresponse(); payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(len(payload['results']), 4)
            self.assertIn('markdown', payload); self.assertIn('html', payload)
            conn.request('POST', '/summarize', '{}', {'Host':'127.0.0.1:8765', 'Origin':'https://attacker.example'})
            response = conn.getresponse(); response.read(); self.assertEqual(response.status, 403)
            conn.request('GET', '/', headers={'Host':'attacker.example'})
            response = conn.getresponse(); response.read(); self.assertEqual(response.status, 403)
            conn.close()
        finally:
            server.shutdown(); server.server_close(); thread.join()

if __name__ == '__main__': unittest.main()
