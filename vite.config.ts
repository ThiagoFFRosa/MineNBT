import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import fs from 'node:fs';
import type { Plugin } from 'vite';

const assetsRoot = path.resolve(__dirname, 'minecraft-assets');
const localMinecraftAssets: Plugin = {
  name: 'local-minecraft-assets',
  configureServer(server) {
    server.middlewares.use('/', (request, response, next) => {
      const match=request.url?.match(/^\/(\d+\.\d+)\/(.+?)(?:\?.*)?$/); if(!match)return next();
      const relative=decodeURIComponent(match[2]); if(relative.includes('..')){response.statusCode=400;return response.end('Invalid path')}
      const file=path.join(assetsRoot,match[1],relative);if(!file.startsWith(assetsRoot+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile())return next();
      response.setHeader('Cache-Control','public, max-age=3600');fs.createReadStream(file).pipe(response);
    });
  },
  closeBundle() { const out=path.resolve(__dirname,'dist');for(const version of fs.readdirSync(assetsRoot)){const source=path.join(assetsRoot,version);if(fs.statSync(source).isDirectory())fs.cpSync(source,path.join(out,version),{recursive:true})} },
};

export default defineConfig({
  plugins: [react(), localMinecraftAssets],
  publicDir: false,
  server: { fs: { allow: [__dirname] } },
  build: { sourcemap: true },
});
