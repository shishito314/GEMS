#pragma once

#include <WiFiNINA.h>
#include "config.h"

class CircularCache {
public:
  CircularCache();
  String cache[CACHE_MAX];
  int cacheBegin{ 0 };
  int cacheEnd{ 0 };
  int newCacheBegin{ 0 };

  void add(const String& newCacheLog);
  void send(const WiFiClient& client);
  void print();
  void clearOldCache();
};

CircularCache::CircularCache() {
  for (int i = 0; i < CACHE_MAX; ++i) {
    cache[i].reserve(MAX_CACHE_ENTRY_SIZE);  // Pre-allocate memory to prevent fragmentation
  }
}

void CircularCache::add(const String& newCacheLog) {
  cache[cacheEnd] = newCacheLog;
  cacheEnd = (cacheEnd + 1) % CACHE_MAX;

  if (cacheEnd == cacheBegin) {
    if (CACHE_MAX < 4) {
      // Just drop the oldest entry
      cacheBegin = (cacheBegin + 1) % CACHE_MAX;
      return;
    }
    for (int i = 0; i < CACHE_MAX / 2; ++i) {  // compaction
      int readIndex = (cacheBegin + i * 2 + 1) % CACHE_MAX;
      int writeIndex = (cacheBegin + i) % CACHE_MAX;
      cache[writeIndex] = cache[readIndex];
    }
    newCacheBegin = (cacheBegin + ((newCacheBegin - cacheBegin + CACHE_MAX) % CACHE_MAX) / 2) % CACHE_MAX;
    cacheEnd = (cacheBegin + CACHE_MAX / 2) % CACHE_MAX;
  }
}

void CircularCache::send(const WiFiClient& client) {
  if (cacheBegin != cacheEnd) {
    int i = cacheEnd - 1;
    while (true) {
      client.print(cache[i]);
      Serial.print(cache[i]);
      if (i == cacheBegin) break;
      i = (i - 1 + CACHE_MAX) % CACHE_MAX;  // decrement with wrap-around
    }
    newCacheBegin = cacheEnd;
  }
}

void CircularCache::print() {
  if (cacheBegin != cacheEnd) {
    int i = cacheEnd - 1;
    while (true) {
      Serial.print(cache[i]);
      Serial.print(" ");
      if (i == cacheBegin) break;
      i = (i - 1 + CACHE_MAX) % CACHE_MAX;  // decrement with wrap-around
    }
    Serial.println("\n");
  }
}

void CircularCache::clearOldCache() {
  cacheBegin = newCacheBegin;
}