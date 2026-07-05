<script lang="ts">
	// R1: 스타일은 src/lib/design/ 에서만 선언한다. 여기서는 import 만.
	import '$lib/design/tokens.css';
	import '$lib/design/base.css';

	let { children } = $props();
</script>

{@render children()}
