<script lang="ts" setup>
import { useUserStore } from '@/stores/user'
import { handleLogout } from '@/services/login'
import ws from '@/services/ws'


const store = useUserStore()

</script>


<template>
    <div class="navbar bg-base-100 border-b border-base-300">
        <div class="flex-1">
            <button @click="ws.match.value.matched = 'waiting'" class="btn btn-ghost text-xl">Chat avec: {{ ws.match.value.opponent.username || '...' }}</button>
        </div>
    <div class="flex-none">
        <div class="dropdown dropdown-end">
        <label tabindex="0" class="btn btn-ghost btn-circle avatar">
            <div class="avatar online">
            <div class="w-36 rounded-full">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full p-1.5 text-base-content/40">
                    <path fill-rule="evenodd" d="M18.685 19.097A9.723 9.723 0 0021.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 003.065 7.097A9.716 9.716 0 0012 21.75a9.716 9.716 0 006.685-2.653zm-12.54-1.285A7.486 7.486 0 0112 15a7.486 7.486 0 015.855 2.812A8.224 8.224 0 0112 20.25a8.224 8.224 0 01-5.855-2.438zM15.75 9a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clip-rule="evenodd" />
                </svg>
            </div>
            </div>
        </label>
        <ul tabindex="0" class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-200 rounded-box w-52">
            <li class="p-2 font-semibold pointer-events-none">
            <span>{{ store.username }}</span>
            </li>
            <li>
            <button @click="handleLogout()" class="flex items-center text-error">
                Logout
            </button>
            </li>
        </ul>
        </div>
    </div>
    </div>
</template>
