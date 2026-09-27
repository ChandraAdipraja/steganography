# Benchmark 5 citra x 3 ukuran pesan

Stego-key: `benchmark-key-123` (dummy tetap untuk reproduksibilitas, bukan secret asli).

| image | resolution | message_size | payload_size | mse | psnr | extraction_ok |
|---|---|---|---|---|---|---|
| cover_01_solid.png | 256x256 | 16 | 60 | 0.001368 | 76.77 | True |
| cover_01_solid.png | 256x256 | 256 | 300 | 0.005920 | 70.41 | True |
| cover_01_solid.png | 256x256 | 1024 | 1068 | 0.021942 | 64.72 | True |
| cover_02_hgradient.png | 256x256 | 16 | 60 | 0.001338 | 76.87 | True |
| cover_02_hgradient.png | 256x256 | 256 | 300 | 0.006134 | 70.25 | True |
| cover_02_hgradient.png | 256x256 | 1024 | 1068 | 0.021927 | 64.72 | True |
| cover_03_vgradient.png | 256x256 | 16 | 60 | 0.001211 | 77.30 | True |
| cover_03_vgradient.png | 256x256 | 256 | 300 | 0.006266 | 70.16 | True |
| cover_03_vgradient.png | 256x256 | 1024 | 1068 | 0.021947 | 64.72 | True |
| cover_04_noise.png | 256x256 | 16 | 60 | 0.001348 | 76.83 | True |
| cover_04_noise.png | 256x256 | 256 | 300 | 0.006322 | 70.12 | True |
| cover_04_noise.png | 256x256 | 1024 | 1068 | 0.022191 | 64.67 | True |
| cover_05_checker.png | 256x256 | 16 | 60 | 0.001322 | 76.92 | True |
| cover_05_checker.png | 256x256 | 256 | 300 | 0.006154 | 70.24 | True |
| cover_05_checker.png | 256x256 | 1024 | 1068 | 0.021667 | 64.77 | True |
