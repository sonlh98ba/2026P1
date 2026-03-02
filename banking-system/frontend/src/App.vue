<template>
  <div class="min-h-screen bg-slate-100 p-6">
    <div class="max-w-6xl mx-auto space-y-6">

      <!-- Header -->
      <div class="bg-white shadow rounded-xl p-6 flex justify-between items-center">
        <h1 class="text-2xl font-bold text-slate-700">
          Mini Banking
        </h1>
      </div>

      <!-- Tabs -->
      <div class="bg-white shadow rounded-xl">
        <div class="flex border-b">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            class="px-6 py-3 font-semibold border-b-2"
            :class="activeTab === tab.key
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Content -->
        <div class="p-6">

          <!-- Accounts Tab -->
          <div v-if="activeTab === 'accounts'">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-semibold">Tài khoản</h2>
              <button
                @click="createAccount"
                class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
              >
                + Tạo tài khoản
              </button>
            </div>

            <table class="w-full border">
              <thead class="bg-slate-50">
                <tr>
                  <th class="border p-2 text-left">Account No</th>
                  <th class="border p-2 text-right">Số dư</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in accounts" :key="a.account_id">
                  <td class="border p-2 font-mono">{{ a.account_no }}</td>
                  <td class="border p-2 text-right font-semibold">
                    {{ formatMoney(a.balance) }} VNĐ
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Transfer Tab -->
          <div v-if="activeTab === 'transfer'" class="max-w-md">
            <h2 class="text-lg font-semibold mb-4">Chuyển tiền</h2>

            <div class="space-y-3">
              <input
                v-model="transfer.from_account_no"
                placeholder="From Account No"
                class="w-full border p-3 rounded-lg"
              />

              <input
                v-model="transfer.to_account_no"
                placeholder="To Account No"
                class="w-full border p-3 rounded-lg"
              />

              <input
                v-model.number="transfer.amount"
                type="number"
                placeholder="Số tiền"
                class="w-full border p-3 rounded-lg"
              />

              <button
                @click="doTransfer"
                class="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold"
              >
                Thực hiện giao dịch
              </button>
            </div>
          </div>

          <!-- History Tab -->
          <div v-if="activeTab === 'history'">
            <h2 class="text-lg font-semibold mb-4">Lịch sử giao dịch</h2>

            <div class="flex gap-2 mb-4 max-w-md">
              <input
                v-model="historyAccountNo"
                placeholder="Account No"
                class="border p-2 rounded-lg w-full"
              />
              <button
                @click="loadHistory"
                class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
              >
                Tra cứu
              </button>
            </div>

            <table v-if="transactions.length" class="w-full border">
              <thead class="bg-slate-50">
                <tr>
                  <th class="border p-2">Thời gian</th>
                  <th class="border p-2">Debit</th>
                  <th class="border p-2">Credit</th>
                  <th class="border p-2">Số dư sau</th>
                  <th class="border p-2">Nội dung</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(t, i) in transactions" :key="i">
                  <td class="border p-2 text-sm">
                    {{ formatTime(t.time) }}
                  </td>
                  <td class="border p-2 text-red-600 font-semibold">
                    {{ t.debit ? '-' + formatMoney(t.debit) : '' }}
                  </td>
                  <td class="border p-2 text-green-600 font-semibold">
                    {{ t.credit ? '+' + formatMoney(t.credit) : '' }}
                  </td>
                  <td class="border p-2 font-semibold text-right">
                    {{ formatMoney(t.balance_after) }}
                  </td>
                  <td class="border p-2 text-sm">
                    {{ t.description }}
                  </td>
                </tr>
              </tbody>
            </table>

            <p v-else class="text-gray-400">
              Chưa có dữ liệu
            </p>
          </div>

        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const API = 'http://localhost:8000/api'

const tabs = [
  { key: 'accounts', label: 'Tài khoản' },
  { key: 'transfer', label: 'Chuyển tiền' },
  { key: 'history', label: 'Lịch sử giao dịch' }
]

const activeTab = ref('accounts')

const accounts = ref([])

const transfer = ref({
  from_account_no: '',
  to_account_no: '',
  amount: 0
})

const historyAccountNo = ref('')
const transactions = ref([])

const createAccount = async () => {
  const res = await axios.post(`${API}/accounts`)
  accounts.value.push(res.data)
}

const doTransfer = async () => {
  await axios.post(`${API}/transfer`, {
    from_account_no: transfer.value.from_account_no,
    to_account_no: transfer.value.to_account_no,
    amount: transfer.value.amount
  })
  alert('Chuyển tiền thành công')
}

const loadHistory = async () => {
  const res = await axios.get(`${API}/transactions/${historyAccountNo.value}`)
  transactions.value = res.data
}

const formatMoney = n =>
  new Intl.NumberFormat('vi-VN').format(n)

const formatTime = t =>
  new Date(t).toLocaleString('vi-VN')
</script>
