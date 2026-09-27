# Benchmark 5 citra x 3 ukuran pesan

Stego-key: `benchmark-key-123` (dummy tetap untuk reproduksibilitas, bukan secret asli).

| image | resolution | message_size | payload_size | mse | psnr | extraction_ok |
|---|---|---|---|---|---|---|
| cover_01_solid.png | 256x256 | 16 | 60 | 0.001226 | 77.25 | True |
| cover_01_solid.png | 256x256 | 256 | 300 | 0.006180 | 70.22 | True |
| cover_01_solid.png | 256x256 | 1024 | 1068 | 0.021500 | 64.81 | True |
| cover_02_hgradient.png | 256x256 | 16 | 60 | 0.001282 | 77.05 | True |
| cover_02_hgradient.png | 256x256 | 256 | 300 | 0.006190 | 70.21 | True |
| cover_02_hgradient.png | 256x256 | 1024 | 1068 | 0.022024 | 64.70 | True |
| cover_03_vgradient.png | 256x256 | 16 | 60 | 0.001394 | 76.69 | True |
| cover_03_vgradient.png | 256x256 | 256 | 300 | 0.006195 | 70.21 | True |
| cover_03_vgradient.png | 256x256 | 1024 | 1068 | 0.021759 | 64.75 | True |
| cover_04_noise.png | 256x256 | 16 | 60 | 0.001348 | 76.83 | True |
| cover_04_noise.png | 256x256 | 256 | 300 | 0.006444 | 70.04 | True |
| cover_04_noise.png | 256x256 | 1024 | 1068 | 0.022013 | 64.70 | True |
| cover_05_checker.png | 256x256 | 16 | 60 | 0.001450 | 76.52 | True |
| cover_05_checker.png | 256x256 | 256 | 300 | 0.006220 | 70.19 | True |
| cover_05_checker.png | 256x256 | 1024 | 1068 | 0.022064 | 64.69 | True |
