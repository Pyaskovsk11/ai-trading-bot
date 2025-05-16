FROM node:18-alpine

WORKDIR /webapp

COPY webapp/package.json ./
COPY webapp/package-lock.json ./
RUN npm install --legacy-peer-deps

COPY ./webapp ./

RUN npm run build

CMD ["npx", "serve", "-s", "build", "-l", "3000"] 