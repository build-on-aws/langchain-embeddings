{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import sys\n",
    "from step_function_utils import send_task_success\n",
    "from video_processor import ffmpeg_check, extract_frames\n",
    "from utils import download_file, parse_location, upload_file\n",
    "from get_image_embeddings import get_images_embeddings\n",
    "from similarity import cosine_similarity_list, filter_relevant_frames\n",
    "\n",
    "tmp_path                    = \"./tmp\"\n",
    "difference_threshold        = 0.9\n",
    "\n",
    "os.environ['S3_URI'] = 's3://you-bucket/video_in/video_corto.mp4'\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "s3://workflow-stack-videobucket6ed8e1af-tei0ss53rkw0/video_in/video_corto.mp4\n"
     ]
    }
   ],
   "source": [
    "s3_uri = os.environ.get(\"S3_URI\", \"s3://bucket/key\")\n",
    "task_token = os.environ.get(\"TASK_TOKEN\", None)\n",
    "\n",
    "print(s3_uri)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Bucket: workflow-stack-videobucket6ed8e1af-tei0ss53rkw0\n",
      "prefix: video_in\n",
      "extension: mp4\n",
      "file: video_corto.mp4\n"
     ]
    }
   ],
   "source": [
    "#ffmpeg_check()\n",
    "\n",
    "# Parse the S3 URI\n",
    "bucket, prefix, fileName, extension, file  = parse_location(s3_uri)\n",
    "\n",
    "# Print bucket and key\n",
    "print(f\"Bucket: {bucket}\")\n",
    "print(f\"prefix: {prefix}\")\n",
    "print(f\"extension: {extension}\")\n",
    "print(f\"file: {file}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "descargando video_corto.mp4 s3://workflow-stack-videobucket6ed8e1af-tei0ss53rkw0/video_in to ./tmp/video_corto.mp4\n",
      "File already exists\n"
     ]
    },
    {
     "data": {
      "text/plain": [
       "True"
      ]
     },
     "execution_count": 4,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "local_path              = f\"{tmp_path}/{file}\"\n",
    "location                = f\"{prefix}/{file}\"\n",
    "output_dir              = f\"{tmp_path}/{fileName}\"\n",
    "\n",
    "# Create directory if it doesn't exist\n",
    "os.makedirs(os.path.dirname(local_path), exist_ok=True)\n",
    "\n",
    "print(f\"descargando {file} s3://{bucket}/{prefix} to {local_path}\")\n",
    "download_file(bucket,location, local_path)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "processing frames...\n",
      "code: 0 stdout:  stderr: ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers\n",
      "  built with Apple clang version 16.0.0 (clang-1600.0.26.6)\n",
      "  configuration: --prefix=/opt/homebrew/Cellar/ffmpeg/7.1.1_1 --enable-shared --enable-pthreads --enable-version3 --cc=clang --host-cflags= --host-ldflags='-Wl,-ld_classic' --enable-ffplay --enable-gnutls --enable-gpl --enable-libaom --enable-libaribb24 --enable-libbluray --enable-libdav1d --enable-libharfbuzz --enable-libjxl --enable-libmp3lame --enable-libopus --enable-librav1e --enable-librist --enable-librubberband --enable-libsnappy --enable-libsrt --enable-libssh --enable-libsvtav1 --enable-libtesseract --enable-libtheora --enable-libvidstab --enable-libvmaf --enable-libvorbis --enable-libvpx --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxml2 --enable-libxvid --enable-lzma --enable-libfontconfig --enable-libfreetype --enable-frei0r --enable-libass --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenjpeg --enable-libspeex --enable-libsoxr --enable-libzmq --enable-libzimg --disable-libjack --disable-indev=jack --enable-videotoolbox --enable-audiotoolbox --enable-neon\n",
      "  libavutil      59. 39.100 / 59. 39.100\n",
      "  libavcodec     61. 19.101 / 61. 19.101\n",
      "  libavformat    61.  7.100 / 61.  7.100\n",
      "  libavdevice    61.  3.100 / 61.  3.100\n",
      "  libavfilter    10.  4.100 / 10.  4.100\n",
      "  libswscale      8.  3.100 /  8.  3.100\n",
      "  libswresample   5.  3.100 /  5.  3.100\n",
      "  libpostproc    58.  3.100 / 58.  3.100\n",
      "Input #0, mov,mp4,m4a,3gp,3g2,mj2, from './tmp/video_corto.mp4':\n",
      "  Metadata:\n",
      "    major_brand     : mp42\n",
      "    minor_version   : 1\n",
      "    compatible_brands: isommp41mp42\n",
      "    creation_time   : 2025-03-25T01:53:05.000000Z\n",
      "  Duration: 00:09:58.08, start: 0.000000, bitrate: 563 kb/s\n",
      "  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(tv, bt709, progressive), 1920x1080, 367 kb/s, 20 fps, 20 tbr, 10240 tbn (default)\n",
      "      Metadata:\n",
      "        creation_time   : 2025-03-25T01:53:05.000000Z\n",
      "        handler_name    : Core Media Video\n",
      "        vendor_id       : [0][0][0][0]\n",
      "  Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 48000 Hz, stereo, fltp, 192 kb/s (default)\n",
      "      Metadata:\n",
      "        creation_time   : 2025-03-25T01:53:05.000000Z\n",
      "        handler_name    : Core Media Audio\n",
      "        vendor_id       : [0][0][0][0]\n",
      "Stream mapping:\n",
      "  Stream #0:0 -> #0:0 (h264 (native) -> mjpeg (native))\n",
      "Press [q] to stop, [?] for help\n",
      "Output #0, image2, to './tmp/video_corto/sec_%05d.jpg':\n",
      "  Metadata:\n",
      "    major_brand     : mp42\n",
      "    minor_version   : 1\n",
      "    compatible_brands: isommp41mp42\n",
      "    encoder         : Lavf61.7.100\n",
      "  Stream #0:0(und): Video: mjpeg, yuv420p(pc, bt709, progressive), 1024x576, q=2-31, 200 kb/s, 1 fps, 1 tbn (default)\n",
      "      Metadata:\n",
      "        creation_time   : 2025-03-25T01:53:05.000000Z\n",
      "        handler_name    : Core Media Video\n",
      "        vendor_id       : [0][0][0][0]\n",
      "        encoder         : Lavc61.19.101 mjpeg\n",
      "      Side data:\n",
      "        cpb: bitrate max/min/avg: 0/0/200000 buffer size: 0 vbv_delay: N/A\n",
      "frame=   88 fps=0.0 q=24.8 size=N/A time=00:01:28.00 bitrate=N/A speed= 174x    \n",
      "frame=  173 fps=172 q=24.8 size=N/A time=00:02:53.00 bitrate=N/A speed= 172x    \n",
      "frame=  261 fps=172 q=24.8 size=N/A time=00:04:21.00 bitrate=N/A speed= 172x    \n",
      "frame=  353 fps=175 q=24.8 size=N/A time=00:05:53.00 bitrate=N/A speed= 175x    \n",
      "frame=  441 fps=175 q=24.8 size=N/A time=00:07:21.00 bitrate=N/A speed= 175x    \n",
      "frame=  531 fps=176 q=24.8 size=N/A time=00:08:51.00 bitrate=N/A speed= 176x    \n",
      "[out#0/image2 @ 0x147e144c0] video:14604KiB audio:0KiB subtitle:0KiB other streams:0KiB global headers:0KiB muxing overhead: unknown\n",
      "frame=  598 fps=179 q=24.8 Lsize=N/A time=00:09:58.00 bitrate=N/A speed= 179x    \n",
      "\n"
     ]
    }
   ],
   "source": [
    "files = extract_frames(local_path, output_dir)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "starting embedding process...\n",
      "0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 236 237 238 239 240 241 242 243 244 245 246 247 248 249 250 251 252 253 254 255 256 257 258 259 260 261 262 263 264 265 266 267 268 269 270 271 272 273 274 275 276 277 278 279 280 281 282 283 284 285 286 287 288 289 290 291 292 293 294 295 296 297 298 299 300 301 302 303 304 305 306 307 308 309 310 311 312 313 314 315 316 317 318 319 320 321 322 323 324 325 326 327 328 329 330 331 332 333 334 335 336 337 338 339 340 341 342 343 344 345 346 347 348 349 350 351 352 353 354 355 356 357 358 359 360 361 362 363 364 365 366 367 368 369 370 371 372 373 374 375 376 377 378 379 380 381 382 383 384 385 386 387 388 389 390 391 392 393 394 395 396 397 398 399 400 401 402 403 404 405 406 407 408 409 410 411 412 413 414 415 416 417 418 419 420 421 422 423 424 425 426 427 428 429 430 431 432 433 434 435 436 437 438 439 440 441 442 443 444 445 446 447 448 449 450 451 452 453 454 455 456 457 458 459 460 461 462 463 464 465 466 467 468 469 470 471 472 473 474 475 476 477 478 479 480 481 482 483 484 485 486 487 488 489 490 491 492 493 494 495 496 497 498 499 500 501 502 503 504 505 506 507 508 509 510 511 512 513 514 515 516 517 518 519 520 521 522 523 524 525 526 527 528 529 530 531 532 533 534 535 536 537 538 539 540 541 542 543 544 545 546 547 548 549 550 551 552 553 554 555 556 557 558 559 560 561 562 563 564 565 566 567 568 569 570 571 572 573 574 575 576 577 578 579 580 581 582 583 584 585 586 587 588 589 590 591 592 593 594 595 596 597 "
     ]
    }
   ],
   "source": [
    "embed_1024 = get_images_embeddings(files, embedding_dimmesion=1024)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "metadata": {},
   "outputs": [],
   "source": [
    "similarity_1024 = cosine_similarity_list(embed_1024)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "metadata": {},
   "outputs": [],
   "source": [
    "similarity_1024.append(0.5) # add this so the last one is pick\n",
    "selected_frames = filter_relevant_frames( similarity_1024, difference_threshold = difference_threshold)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "[2, 236, 288, 326, 351, 420, 539, 595, 597]"
      ]
     },
     "execution_count": 9,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "selected_frames"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "./tmp/video_corto/sec_00003.jpg => video_in/selected_frames/3.jpg\n",
      "File uploaded successfully\n",
      "./tmp/video_corto/sec_00237.jpg => video_in/selected_frames/237.jpg\n",
      "File uploaded successfully\n",
      "./tmp/video_corto/sec_00289.jpg => video_in/selected_frames/289.jpg\n",
      "File uploaded successfully\n",
      "./tmp/video_corto/sec_00327.jpg => video_in/selected_frames/327.jpg\n",
      "File uploaded successfully\n",
      "./tmp/video_corto/sec_00352.jpg => video_in/selected_frames/352.jpg\n",
      "File uploaded successfully\n",
      "./tmp/video_corto/sec_00421.jpg => video_in/selected_frames/421.jpg\n",
      "File uploaded successfully\n",
      "./tmp/video_corto/sec_00540.jpg => video_in/selected_frames/540.jpg\n",
      "File uploaded successfully\n",
      "./tmp/video_corto/sec_00596.jpg => video_in/selected_frames/596.jpg\n",
      "File uploaded successfully\n",
      "./tmp/video_corto/sec_00598.jpg => video_in/selected_frames/598.jpg\n",
      "File uploaded successfully\n"
     ]
    }
   ],
   "source": [
    "\n",
    "selected_frames_real = []\n",
    "\n",
    "for sf in selected_frames:\n",
    "\n",
    "    origen_file = f\"{output_dir}/sec_{str(sf+1).zfill(5)}.jpg\"\n",
    "    real_frame = sf + 1\n",
    "    destination_key = f\"{prefix}/selected_frames/{real_frame}.jpg\"\n",
    "\n",
    "    print(f\"{origen_file} => {destination_key}\")\n",
    "    upload_file(bucket, destination_key, origen_file)\n",
    "    selected_frames_real.append(real_frame)\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": ".venv",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.13.2"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
