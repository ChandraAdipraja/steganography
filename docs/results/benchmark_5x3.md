# Benchmark 5 citra x 3 ukuran pesan

Stego-key: `benchmark-key-123` (dummy tetap untuk reproduksibilitas, bukan secret asli).

| image | resolution | message_size | payload_size | mse | psnr | extraction_ok |
|---|---|---|---|---|---|---|
| cover_01_solid.png | 256x256 | 16 | 60 | 0.001307 | 76.97 | True |
| cover_01_solid.png | 256x256 | 256 | 300 | 0.006256 | 70.17 | True |
| cover_01_solid.png | 256x256 | 1024 | 1068 | 0.021983 | 64.71 | True |
| cover_02_hgradient.png | 256x256 | 16 | 60 | 0.001455 | 76.50 | True |
| cover_02_hgradient.png | 256x256 | 256 | 300 | 0.006109 | 70.27 | True |
| cover_02_hgradient.png | 256x256 | 1024 | 1068 | 0.021851 | 64.74 | True |
| cover_03_vgradient.png | 256x256 | 16 | 60 | 0.001282 | 77.05 | True |
| cover_03_vgradient.png | 256x256 | 256 | 300 | 0.006119 | 70.26 | True |
| cover_03_vgradient.png | 256x256 | 1024 | 1068 | 0.021978 | 64.71 | True |
| cover_04_noise.png | 256x256 | 16 | 60 | 0.001343 | 76.85 | True |
| cover_04_noise.png | 256x256 | 256 | 300 | 0.006185 | 70.22 | True |
| cover_04_noise.png | 256x256 | 1024 | 1068 | 0.021805 | 64.75 | True |
| cover_05_checker.png | 256x256 | 16 | 60 | 0.001338 | 76.87 | True |
| cover_05_checker.png | 256x256 | 256 | 300 | 0.006343 | 70.11 | True |
| cover_05_checker.png | 256x256 | 1024 | 1068 | 0.022018 | 64.70 | True |
