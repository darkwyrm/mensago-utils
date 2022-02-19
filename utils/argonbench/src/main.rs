use argon2::{self, Config, ThreadMode, Variant, Version};
use rand::Rng;
use stopwatch::{Stopwatch};

fn hashbench() {
	let password = "MyS3cretPassw*rd";
	let salt = rand::thread_rng().gen::<[u8; 16]>();

	let testlist = [
		(0x10000, 1, 2), // 64K
		(0x20000, 1, 2), // 128K
		(0x40000, 1, 2), // 256K
		(0x80000, 1, 2), // 512K
		(0x100_000, 1, 2), // 1MiB
		(0x200_000, 1, 2), // 2MiB

		(0x10000, 1, 4), // 64K
		(0x20000, 1, 4), // 128K
		(0x40000, 1, 4), // 512K
		(0x80000, 1, 4), // 256K
		(0x100_000, 1, 4), // 1MiB
		(0x200_000, 1, 4), // 2MiB

		(0x10000, 2, 2), // 64K
		(0x20000, 2, 2), // 128K
		(0x40000, 2, 2), // 256K
		(0x80000, 2, 2), // 512K
		(0x100_000, 2, 2), // 1MiB
		(0x200_000, 2, 2), // 2MiB
	];
	
	for test in testlist {
		let config = Config {
			variant: Variant::Argon2id,
			version: Version::Version13,
			mem_cost: test.0, // 64K
			time_cost: test.1,
			lanes: test.2,
			thread_mode: ThreadMode::Parallel,
			secret: &[],
			ad: &[],
			hash_length: 32
		};
		let sw = Stopwatch::start_new();
		argon2::hash_encoded(password.as_bytes(), &salt, &config).unwrap();
		let elapsed = sw.elapsed_ms();

		println!("Test: M:{} T: {}, P:{}\t {}ms", test.0, test.1, test.2, elapsed);
	}
}

fn main() {
	hashbench();
}
