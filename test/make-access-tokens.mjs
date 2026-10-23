// Test-only: a stand-in for Cloudflare Access. Writes the public key set Documate fetches
// (<out>/www/cdn-cgi/access/certs) and a set of signed tokens (<out>/tokens.env), some deliberately bad.
import { createSign, generateKeyPairSync } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';

const [out, iss, aud] = process.argv.slice(2);
const good = generateKeyPairSync('rsa', { modulusLength: 2048 });
const other = generateKeyPairSync('rsa', { modulusLength: 2048 });
const jwk = { ...good.publicKey.export({ format: 'jwk' }), kid: 'test-key', alg: 'RS256', use: 'sig' };

mkdirSync(`${out}/www/cdn-cgi/access`, { recursive: true });
writeFileSync(`${out}/www/cdn-cgi/access/certs`, JSON.stringify({ keys: [jwk] }));

const b64 = (value) => Buffer.from(JSON.stringify(value)).toString('base64url');
const now = Math.floor(Date.now() / 1000);
const claims = (email, extra = {}) => ({ iss, aud: [aud], email, iat: now, nbf: now, exp: now + 3600, type: 'app', sub: 'test', ...extra });
const sign = (body, key = good.privateKey) => {
  const head = b64({ alg: 'RS256', kid: 'test-key', typ: 'JWT' });
  const payload = b64(body);
  return `${head}.${payload}.${createSign('RSA-SHA256').update(`${head}.${payload}`).sign(key).toString('base64url')}`;
};

writeFileSync(
  `${out}/tokens.env`,
  [
    `T_EXISTING=${sign(claims('owner@example.com'))}`,
    `T_NEW=${sign(claims('newbie@example.com'))}`,
    `T_OTHER_DOMAIN=${sign(claims('someone@elsewhere.test'))}`,
    `T_WRONG_SIGNER=${sign(claims('owner@example.com'), other.privateKey)}`,
    `T_WRONG_AUD=${sign(claims('owner@example.com', { aud: ['another-app'] }))}`,
    `T_EXPIRED=${sign(claims('owner@example.com', { exp: now - 600 }))}`,
  ].join('\n') + '\n',
);
